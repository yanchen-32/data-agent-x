# 独立订单队列参考计算

本目录供开发复核，不属于 `src/dataagentx` 生产包，也不作为模型可执行工具。

`cohort.py` 的 `calculate_reference(input)` 只接收小型合成 Fixture 的输入，使用标准库独立实现半开支付窗口、逐单成熟、水位覆盖、同单成功退款计数及精确 `Fraction` 比率。前提不足时阻断并返回空业务指标，候选订单仍可用于诊断。

在仓库根目录运行：

```python
import json
from pathlib import Path
from reference.cohort import calculate_reference

fixture = json.loads(Path(
    "tests/fixtures/order_boundaries/02_utc_boundaries.json"
).read_text(encoding="utf-8"))
actual = calculate_reference(fixture["input"])
print(actual["metrics"]["baseline"])
# N=2、U=1、rate=Fraction(1, 2)
```

运行 `.venv/bin/python -m pytest tests/test_reference_cohort.py` 验证参考计算。实际输出与[先行保存的逐单复算](manual_checks/2026-10-14.md)、[静态数值记录](manual_checks/2026-10-14.json)及原 Fixture 预期对照，不用参考函数生成预期。

输入约束：固定单域、单快照，字段结构已核验，支持全域或单地区过滤；重复订单/事件、域快照混入、孤立及支付前退款抛出 `ValueError`。函数不判断访问权限、维度目录、导入批准或完整质量规则，也没有数据库、SQL、生产状态机或贡献分解。返回结构仅用于本地参考，不是调查 API 契约。

未来生产实现应独立编写，并与这些固定预期比较，不能导入本参考函数作为其业务实现，否则失去对照独立性。
