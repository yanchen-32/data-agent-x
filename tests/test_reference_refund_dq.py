import copy
import hashlib
import json
from pathlib import Path

import pytest

from reference.cohort import calculate_reference


ROOT = Path(__file__).resolve().parents[1]
DRAFTS = ROOT / "reference" / "fixture_drafts"


@pytest.mark.parametrize(
    ("filename", "expected_sha256", "message"),
    [
        pytest.param(
            "m04_01_duplicate_refund_event.json",
            "56f61c74eb07b6df94e294a68f32791eb4f0f4c9ad8d6eee6e3934d10967952e",
            "重复退款事件",
            id="M04-01",
        ),
        pytest.param(
            "m04_02_orphan_refund.json",
            "0787622080be1bd10a8a10e2a8e83bec42201671edc5981da3fff26aae68c226",
            "孤立退款",
            id="M04-02",
        ),
        pytest.param(
            "m04_03_refund_before_payment.json",
            "cb8a24516c2792db82653a07c848cdcee36565212a71a336e843ed6955605d1a",
            "退款早于支付",
            id="M04-03",
        ),
    ],
)
def test_reference_rejects_single_refund_fault(
    filename: str, expected_sha256: str, message: str,
) -> None:
    path = DRAFTS / filename
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected_sha256
    data = json.loads(raw)["input"]
    before = copy.deepcopy(data)

    # 正常返回比较对象、未抛异常或命中其他故障均会使测试失败。
    try:
        with pytest.raises(ValueError, match=f"^{message}$"):
            calculate_reference(data)
    finally:
        assert data == before
        assert path.read_bytes() == raw


def test_reference_rejects_missing_required_refund_time() -> None:
    path = ROOT / "tests/fixtures/order_boundaries/07_same_label_distinct_category_ids.json"
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == "e03a1c005e6f99f5e497e452bb3de5e75aa2096f83106f730a45ebcbbec737ac"
    data = copy.deepcopy(json.loads(raw)["input"])
    event, = [row for row in data["refunds"] if row["source_row_id"] == "r07-refund-a-c1"]
    del event["refund_at"]
    before = copy.deepcopy(data)

    try:
        with pytest.raises(ValueError, match="退款缺少必需时间 refund_at") as error:
            calculate_reference(data)
        assert "refund_id=SR-A-C1" in str(error.value)
        assert "source_row_id=r07-refund-a-c1" in str(error.value)
    finally:
        assert data == before
        assert path.read_bytes() == raw
