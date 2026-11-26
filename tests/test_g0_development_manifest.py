import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
CHECKS = ROOT / "reference/regression_checks"
SCRIPT = CHECKS / "check_g0_development_manifest.py"
MANIFEST = CHECKS / "G0_development_manifest.json"


def run_check(*arguments):
    return subprocess.run(
        [sys.executable, "-I", "-B", str(SCRIPT), *map(str, arguments)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_current_development_manifest_passes():
    result = run_check()
    assert result.returncode == 0, result.stderr
    assert "G0 证据检查通过" in result.stdout


@pytest.mark.parametrize(
    ("change", "message"),
    (
        ("file_hash", "文件 SHA-256 不一致"),
        ("expected_hash", "canonical_sha256 不一致"),
        ("recipe_hash", "变体输入 SHA-256 不一致"),
        ("region_hash", "地区变体输入指纹与冻结记录不一致"),
        ("swapped_oracle", "固定预期缺少与输入的关联"),
        ("unregistered_review", "必需证据缺少文件指纹登记"),
        ("unconfirmed_approval", "禁止标记 approved"),
        ("missing_user_confirmation", "缺少本人签收回执"),
        ("wrong_case_confirmation", "本人签收回执绑定到其他用例"),
        ("missing_passed_node", "执行记录缺少 PASSED"),
    ),
)
def test_rejects_inconsistent_manifest_copy(tmp_path, change, message):
    manifest = json.loads(MANIFEST.read_bytes())
    first, second = manifest["main_fixtures"][:2]
    if change == "file_hash":
        manifest["artifacts"][first["input"]["path"]] = "0" * 64
    elif change == "expected_hash":
        first["expected"]["locator"]["canonical_sha256"] = "0" * 64
    elif change in {"recipe_hash", "region_hash"}:
        case_id = "A3-01-EQUAL" if change == "recipe_hash" else "RG01.W"
        record = next(case for case in manifest["control_variants"] if case["case_id"] == case_id)
        record["input"]["canonical_sha256"] = "0" * 64
    elif change == "swapped_oracle":
        first["expected"] = second["expected"]
    elif change == "unregistered_review":
        del manifest["artifacts"][first["review"]["records"][0]]
    elif change == "unconfirmed_approval":
        first["review"]["user_independent_acceptance"] = "pending_user_confirmation"
        first["review"].pop("user_confirmation", None)
        first["review"]["approval_status"] = "approved"
    elif change == "missing_user_confirmation":
        first["review"]["user_independent_acceptance"] = "confirmed_by_user"
        first["review"].pop("user_confirmation", None)
    elif change == "wrong_case_confirmation":
        signed = next(case for case in manifest["main_fixtures"] if case["case_id"] == "A3-06")
        first["review"]["user_independent_acceptance"] = "confirmed_by_user"
        first["review"]["user_confirmation"] = signed["review"]["user_confirmation"]
    elif change == "missing_passed_node":
        first["test_evidence"][0]["node_ids"] = ["test_unrecorded"]

    copy = tmp_path / MANIFEST.name
    copy.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    result = run_check("--manifest", copy)
    assert result.returncode == 1
    assert message in result.stderr


def test_rejects_missing_execution_log_in_copied_evidence(tmp_path):
    manifest = json.loads(MANIFEST.read_bytes())
    for name in manifest["artifacts"]:
        source = ROOT / name
        destination = tmp_path / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    missing = manifest["execution"]["log"]
    (tmp_path / missing).unlink()

    result = run_check("--root", tmp_path, "--manifest", MANIFEST)
    assert result.returncode == 1
    assert f"缺少证据文件 {missing}" in result.stderr
