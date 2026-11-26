"""只读校验 G0 开发数据清单 v1 的证据与绑定。"""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys


MANIFEST = "reference/regression_checks/G0_development_manifest.json"
CASE_GROUPS = ("main_fixtures", "historical_fixtures", "control_variants", "derived_oracles")
EXPECTED_LOCATORS = {
    "frozen_json": "canonical_sha256",
    "manual_case_record": "canonical_sha256",
    "assertions_without_separately_frozen_output": "span_sha256",
    "design_only": "canonical_sha256",
    "manual_blocking_expectation": "line_sha256",
    "rule_derived_blocking_expectation": "line_sha256",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical_sha256(value):
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def json_pointer(value, pointer):
    require(pointer == "" or pointer.startswith("/"), f"无效 JSON 指针 {pointer!r}")
    for part in pointer.split("/")[1:]:
        require(not re.search(r"~(?![01])", part), f"无效 JSON 指针 {pointer!r}")
        key = part.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            require(re.fullmatch(r"0|[1-9][0-9]*", key), f"无效数组索引 {key!r}")
            value = value[int(key)]
        else:
            value = value[key]
    return value


def approved_marker(value):
    if isinstance(value, dict):
        return value.get("approved") is True or any(map(approved_marker, value.values()))
    if isinstance(value, list):
        return any(map(approved_marker, value))
    return value == "approved"


class Evidence:
    def __init__(self, root, artifacts):
        self.root = root.resolve()
        self.files = {}
        self.digests = artifacts
        self.documents = {}

    def verify_files(self):
        for name, digest in self.digests.items():
            relative = Path(name)
            path = (self.root / relative).resolve()
            require(not relative.is_absolute() and path.is_relative_to(self.root),
                    f"证据路径超出仓库 {name}")
            require(path.is_file(), f"缺少证据文件 {name}")
            data = path.read_bytes()
            require(hashlib.sha256(data).hexdigest() == digest, f"文件 SHA-256 不一致 {name}")
            self.files[name] = data

    def file(self, name):
        require(name in self.files, f"必需证据缺少文件指纹登记 {name}")
        return self.files[name]

    def document(self, name):
        if name not in self.documents:
            self.documents[name] = json.loads(self.file(name))
        return self.documents[name]

    def locate(self, locator, fingerprint):
        name = locator["path"]
        value = None
        if fingerprint == "canonical_sha256":
            pointer = locator["pointer"]
            value = json_pointer(self.document(name), pointer)
            actual = canonical_sha256(value)
            label = f"{name}#{pointer}"
        else:
            lines = self.file(name).decode("utf-8").splitlines()
            if fingerprint == "line_sha256":
                first = last = locator["line"]
            else:
                first, last = locator["start_line"], locator["end_line"]
            label = f"{name}:{first}-{last}"
            require(type(first) is int and type(last) is int and 1 <= first <= last <= len(lines),
                    f"证据行号越界 {label}")
            segment = "\n".join(lines[first - 1:last])
            if fingerprint == "span_sha256":
                symbol = locator["symbol"]
                require(re.search(rf"(?m)^def {re.escape(symbol)}\(", segment),
                        f"源码片段缺少符号 {symbol}，位置 {label}")
            actual = hashlib.sha256(segment.encode("utf-8")).hexdigest()
        require(actual == locator[fingerprint], f"{fingerprint} 不一致 {label}")
        return value


def bound_input(case, parent, evidence):
    binding = case["input"]
    if "recipe" not in binding:
        return evidence.locate(binding, "canonical_sha256")
    recipe = binding["recipe"]
    record = evidence.locate(recipe, "line_sha256" if "line" in recipe else "canonical_sha256")
    if isinstance(record, dict) and "input_sha256" in record:
        # 地区变体的哈希已冻结于带指纹的变更记录。
        require(record["input_sha256"] == binding["canonical_sha256"], "地区变体输入指纹与冻结记录不一致")
        return None

    data = deepcopy(parent)
    materialization = binding["materialization"]
    if materialization == "对象字段路径覆盖":
        for path, value in record.items():
            *keys, field = path.split(".")
            target = data
            for key in keys:
                target = target[key]
            target[field] = value
    elif materialization == "清空地区过滤":
        data["context"]["filters"]["region_ids"] = []
    elif materialization == "仅删除来源 r07-refund-a-c1 的 refund_at":
        event, = (row for row in data["refunds"] if row["source_row_id"] == "r07-refund-a-c1")
        del event["refund_at"]
    elif materialization == "按来源记录重放" and "additional_refund" in record:
        scope = evidence.document(recipe["path"])["scope"]
        data["refunds"].append({**scope, **record["additional_refund"]})
    elif materialization == "按来源记录重放":
        for field, value in record.get("context_overrides", {}).items():
            if field == "watermark":
                data["context"][field].update(value)
            else:
                data["context"][field] = value
        for order in data["orders"]:
            if order["order_id"] in record.get("disable_order_ids", []):
                order["is_payment_valid"] = False
        data["refunds"] = [
            row for row in data["refunds"] if row["refund_id"] not in record.get("remove_refund_ids", [])
        ]
    else:
        raise ValueError(f"未知的输入变体构造方式 {materialization}")
    require(canonical_sha256(data) == binding["canonical_sha256"], "重放后的变体输入 SHA-256 不一致")
    return data


def check_expected(case, evidence):
    expected = case["expected"]
    kind = expected["kind"]
    locator = expected["locator"]
    value = evidence.locate(locator, EXPECTED_LOCATORS[kind])
    binding = case["input"]
    if kind in {"assertions_without_separately_frozen_output", "design_only"}:
        evidence.file(expected["manual_basis"])
    if kind == "manual_case_record":
        require(locator == binding["recipe"], "人工预期与输入配方没有绑定到同一条记录")
        publication = expected["publication"]
        evidence.locate(publication, "canonical_sha256")
        shared_path = evidence.document(locator["path"]).get("source_expected")
        if shared_path is None:
            shared_path = evidence.document(locator["path"])["expected_result_ref"].split("#", 1)[0]
        publication_targets = {
            "blocked": (locator["path"], "/blocked_publication"),
            "zero_baseline": (locator["path"], "/zero_baseline_publication"),
            "frozen": (shared_path, "/expected"),
        }
        require((publication["path"], publication["pointer"]) == publication_targets[value.get("publication", "frozen")],
                "人工预期引用了不同的发布结果")
    if kind == "design_only":
        require(locator == binding["recipe"], "设计预期与输入配方没有绑定到同一条记录")
    if kind == "frozen_json":
        pointer = locator["pointer"]
        if binding.get("path") == locator["path"]:
            require(pointer == "/expected", "固定输入应绑定同一 Fixture 的 /expected")
        elif pointer.startswith("/cases/"):
            require(pointer == f"/cases/{case['case_id']}/expected", "预期指向另一用例")
        elif case.get("base_case_id"):
            source = evidence.document(locator["path"])["sources"]["fixture"]
            require(source["path"] == binding["path"] and source["input_sha256"] == binding["canonical_sha256"]
                    and source["sha256"] == evidence.digests[binding["path"]], "衍生 Oracle 的来源绑定不一致")
        elif "recipe" in binding and binding["recipe"]["path"] == locator["path"]:
            require(pointer == binding["recipe"]["pointer"].removesuffix("/input_overrides") + "/expected",
                    "条件变体与预期没有绑定到同一条记录")
        elif "recipe" in binding:
            require(pointer == "/expected/unfiltered_counterexample", "全地区变体没有绑定到冻结反例")
        else:
            raise ValueError("固定预期缺少与输入的关联")
    if "independent_record" in expected:
        record = expected["independent_record"]
        evidence.locate(record, "canonical_sha256")
        require(record["canonical_sha256"] == locator["canonical_sha256"]
                and evidence.document(record["path"])["input_sha256"] == binding["canonical_sha256"],
                "独立 Oracle 与固定输入或预期不一致")
    if "shared_oracle" in expected:
        evidence.locate(expected["shared_oracle"], "canonical_sha256")


def check_test_evidence(entries, suites, passed):
    for entry in entries:
        source = suites[entry["suite"]]["path"]
        require(entry["node_ids"], f"{source} 缺少测试节点")
        for node in entry["node_ids"]:
            require(f"{source}::{node}" in passed, f"执行记录缺少 PASSED {source}::{node}")


def check_user_acceptance(case, evidence):
    review = case["review"]
    status = review["user_independent_acceptance"]
    confirmation = review.get("user_confirmation")
    if status == "pending_user_confirmation":
        require(confirmation is None, "待签收条目带有本人签收回执")
        return

    require(status == "confirmed_by_user", "未知的本人签收状态")
    require(confirmation is not None, "缺少本人签收回执")
    require(confirmation["pointer"] == f"/cases/{case['case_id']}", "本人签收回执绑定到其他用例")
    binding = evidence.locate(confirmation, "canonical_sha256")
    receipt = evidence.document(confirmation["path"])
    require(receipt["source"] == "explicit_user_confirmation", "本人签收缺少明确用户确认")
    review_record = receipt["review_record"]
    require(review_record["path"] in review["records"]
            and evidence.digests.get(review_record["path"]) == review_record["sha256"],
            "本人签收回执与审阅记录未绑定")
    expected = case["expected"]
    require(binding["input_sha256"] == case["input"]["canonical_sha256"]
            and binding["expected_sha256"] == expected["locator"][EXPECTED_LOCATORS[expected["kind"]]],
            "本人签收回执与输入或预期版本不一致")


def check_manifest(manifest, root):
    require(manifest["manifest_id"] == "G0-development" and manifest["manifest_version"] == 1,
            "不支持的开发清单版本")
    require(not approved_marker(manifest), "开发清单 v1 用于证据登记，禁止标记 approved")
    evidence = Evidence(root, manifest["artifacts"])
    evidence.verify_files()
    evidence.file(manifest["inventory_source"]["path"])
    execution = manifest["execution"]
    log = evidence.file(execution["log"]).decode("utf-8")
    evidence.file(execution["config"])
    evidence.file(execution["prior_local_closure_log"])
    passed = {line.removeprefix("PASSED ") for line in log.splitlines() if line.startswith("PASSED ")}
    require(execution["exit_code"] == 0 and "退出码：0" in log.splitlines()
            and len(passed) == execution["passed"], "执行记录的通过数量或退出码不一致")

    rules = manifest["rule_sets"]
    for rule in rules.values():
        require(rule["documents"], "规则集缺少文档")
        for path in rule["documents"]:
            evidence.file(path)
        if "inherits" in rule:
            require(rule["inherits"] in rules, f"缺少继承规则 {rule['inherits']}")
    implementations = manifest["reference_implementations"]
    for implementation in implementations.values():
        evidence.file(implementation["path"])
        require(re.fullmatch(r"[0-9a-f]{40}", implementation["commit"]), "实现版本缺少完整提交 ID")
    suites = manifest["test_suites"]
    for suite in suites.values():
        evidence.file(suite["path"])
        require(suite["execution_id"] == execution["id"], "测试套件未绑定执行记录")
        require(set(suite["implementation_ids"]) <= implementations.keys(), "测试套件引用未知实现")
    logged_digests = {path: digest for digest, path in re.findall(r"(?m)^([0-9a-f]{64})  (.+)$", log)}
    execution_paths = [execution["config"], *(entry["path"] for entry in implementations.values()),
                       *(suite["path"] for suite in suites.values())]
    for path in execution_paths:
        require(logged_digests.get(path) == evidence.digests[path], f"执行记录中的 SHA-256 不一致 {path}")
    require(f"公开源码对照提交：{execution['public_source_anchor']}" in log.splitlines(),
            "执行记录中的公开源码版本不一致")

    inputs = {}
    counts = {group: len(manifest[group]) for group in (*CASE_GROUPS, "indexed_test_only_families")}
    controls = manifest["control_variants"]
    counts["control_variants_with_direct_test"] = sum(bool(case["test_evidence"]) for case in controls)
    counts["control_variants_without_direct_test"] = len(controls) - counts["control_variants_with_direct_test"]
    require(manifest["counts"] == counts, "清单计数与用例记录不一致")
    for group in CASE_GROUPS:
        for case in manifest[group]:
            case_id = case["case_id"]
            try:
                require(case_id not in inputs, "重复用例 ID")
                binding = case["input"]
                parent = inputs[binding["base_case_id"]] if "recipe" in binding else None
                inputs[case_id] = bound_input(case, parent, evidence)
                require(case["rule_set"] in rules, "引用未知规则集")
                if "path" in binding:
                    fixture_id = evidence.document(binding["path"])["case_id"]
                    expected_id = case.get("base_case_id", case_id)
                    if group == "historical_fixtures":
                        expected_id = case_id.removesuffix(f"-v{case['fixture_revision']}")
                    require(fixture_id == expected_id and binding["pointer"] == "/input",
                            "输入定位器与用例身份不一致")
                check_expected(case, evidence)
                if "base_case_id" in case:
                    require(inputs[case_id] == inputs[case["base_case_id"]], "衍生 Oracle 引用了不同输入")
                for field in ("inventory_locator", "prior_draft"):
                    if field in case:
                        evidence.locate(case[field], "canonical_sha256")

                review = case["review"]
                design_only = case["expected"]["kind"] == "design_only"
                technical = "documented_not_executed" if design_only else "technical_review_recorded"
                require(review["technical"] == technical, "技术审阅状态与证据类型不一致")
                require(review["records"], "缺少必需审阅记录")
                for record in review["records"]:
                    evidence.file(record)
                check_user_acceptance(case, evidence)

                tests = case["test_evidence"]
                require(bool(tests) != design_only, "测试证据与设计状态不一致")
                coverage = "no_direct_execution" if design_only else "direct_test_passed"
                require(case.get("reference_coverage", coverage) == coverage, "直接回归状态与测试证据不一致")
                check_test_evidence(tests, suites, passed)
            except (ValueError, KeyError, IndexError, TypeError, AttributeError) as error:
                raise ValueError(f"{case_id}：{error}") from error

    for family in manifest["indexed_test_only_families"]:
        require(family["base_case_id"] in inputs, f"{family['id']} 缺少基础用例")
        evidence.file(family["review_record"])
        require(family["test_evidence"], f"{family['id']} 缺少必需测试证据")
        check_test_evidence(family["test_evidence"], suites, passed)
    for other in manifest["other_evidence"].values():
        if isinstance(other, str):
            evidence.file(other)
        else:
            evidence.locate(other, "canonical_sha256")
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2],
                        help="证据文件所在的仓库根目录")
    parser.add_argument("--manifest", type=Path, help="指定要校验的清单文件，默认使用根目录中的开发清单")
    args = parser.parse_args()
    try:
        manifest_path = args.manifest if args.manifest is not None else args.root / MANIFEST
        manifest = json.loads(manifest_path.read_bytes())
        counts = check_manifest(manifest, args.root)
    except (OSError, ValueError, KeyError, IndexError, TypeError, AttributeError) as error:
        print(f"G0 证据检查失败：{error}", file=sys.stderr)
        return 1
    print(f"G0 证据检查通过（{len(manifest['artifacts'])} 个文件，{counts['main_fixtures']} 个主例，"
          f"{counts['control_variants']} 个控制变体，{counts['derived_oracles']} 个衍生 Oracle）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
