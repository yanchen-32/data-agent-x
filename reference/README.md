# 独立订单队列与类别分组参考计算

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

A3-04/05 的[人工可复核记录](manual_checks/A3-04_A3-05_review.md)复用既有证据，核对原始来源行、成熟与水位、地区 Scope、诊断值和发布值，并保存文件完整性核验信息；不代表用户已独立验收。

输入约束：固定单域、单快照，字段结构已核验，支持全域或单地区过滤；重复订单/事件、域快照混入、孤立及支付前退款抛出 `ValueError`。函数不判断访问权限、维度目录、导入批准或完整质量规则，也没有数据库、SQL、生产状态机或贡献分解。返回结构仅用于本地参考，不是调查 API 契约。

## 最小类别分组参考计算

`category_cohort.py` 的 `calculate_category_reference(input)` 只依赖标准库及既有总体参考函数。它复用 `calculate_reference()` 的输入检查、候选支付队列、成熟/水位和空窗阻断，不修改旧函数的代码、返回结构或业务语义；然后从原始退款重建合格退款订单集合，并从订单及产品目录实际计算类别分组。两个参考函数共享总体前提，不宣称它们是两套完全独立的总体算法；它们与未来生产实现保持独立。

订单按 `(domain_id,snapshot_id,product_id)` 关联产品，以 `category_id` 为分组键；退款按 `(domain_id,snapshot_id,order_id)` 归属订单，同单多笔合格退款只计一次。类别目录 `categories` 是本地展示名约定，通过类别复合键提供 `group_label`，不参与身份或计数。同名不同ID不合并；已知ID缺展示名时保留ID、label为None。所有输入订单必须成功关联产品，缺失产品复合键抛出 `ValueError` 并定位订单/来源；只有合法产品的非关键类别ID缺失才进入 `__unknown__`，不丢弃订单。局部产品和类别目录须属于固定域/快照，重复键或范围混入抛出 `ValueError`，不是生产DQ状态映射。

```python
from reference.category_cohort import calculate_category_reference

fixture = json.loads(Path(
    "tests/fixtures/order_boundaries/07_same_label_distinct_category_ids.json"
).read_text(encoding="utf-8"))
actual = calculate_category_reference(fixture["input"])
assert len(actual["aggregate_rows"]) == 6  # 四条类别行与两条总计行
```

新结果保留总体参考函数的字段，另增加：

- `aggregate_rows`：按窗口排列，先总计，再按类别ID排序；字段沿用 `AggregateRow`，但率是内存中的 `Fraction`，尚未序列化成正式十进制字符串。总计三个身份字段均为None；只输出该窗口实际有候选订单的类别，不为缺席类别补造零率行。
- `group_order_ids`、`group_refunded_order_ids`：按窗口、类别ID记录订单台账，供互斥穷尽、去重及来源追溯检查，不是正式API字段。

比较前提不足时，`aggregate_rows=[]`、两个分组台账为空字典；总体 `metrics` 仍为空业务指标，候选订单仅作诊断，不借分组发布被阻断的比较。

运行 `.venv/bin/python -B -m pytest tests/test_reference_category_cohort.py`。测试只把 `input` 传入计算函数，在测试端与冻结六行预期对照；通过深拷贝核对输入不变，并用拒绝访问 `expected` 的映射检查计算不依赖静态答案。覆盖同名组、产品关联、来源台账、汇总、退款去重与时间边界、地区过滤、未知保留、目录异常及比较阻断。实际运行与剩余边界见 [A3-07 分组回归记录](regression_checks/A3-07_category.md)。

此处未实现生产SQL、授权、批准导入、目录服务、正式输出序列化或贡献分解，也未新增框架。创建阶段的静态检查及其历史待补清单保留原样，新增计算覆盖单独记录；不改写Fixture或先行人工预期来迎合实现。

A3-08 版本定位：当前 `08_category_entry_exit.json` 是面向后续非平凡贡献测试的v2新快照，先行逐单输入与来源见 [v2台账](manual_checks/A3-08_v2.md)。旧版原字节保存在 `08_category_entry_exit.v1.json`，原有3项计算回归加1项SHA-256绑定继续核对v1及其独立JSON台账，不修改冻结hash或旧数值。两版均保留A/shared、B/exit、C/entry；v2让共享组的率及支付占比变化，并让退出、新增组均有有效退款。v2已先保存独立预期，再实际调用参考函数核对六行结果及总计变化，全部一致，见 [v2冻结与执行记录](manual_checks/A3-08_v2_expected.md)；现已新增四项v2专门pytest计算回归，复用既有辅助函数并绑定冻结哈希，执行证据见 [v2回归记录](regression_checks/A3-08_v2.md)，v1原四项保持通过。旧数值与执行证据见 [v1回归记录](regression_checks/A3-08.md)。缺席组不补行，暂不计算贡献分解，也不代表生产批准或用户签字。

A3-09 固定样例 `09_unknown_category_preserved.json` 保存合法产品关联下的非关键未知类别：product_unknown存在且复合键唯一，仅category_id为null；两窗同时包含已知组与__unknown__组且退款率不同。先行逐单预期、来源和实际静态运行记录见 [A3-09说明](manual_checks/A3-09.md)。现已新增一项固定Fixture参考计算回归：先保存 [独立台账](manual_checks/A3-09_expected.json)，再直接从input计算并与台账/静态预期三方比较，六行精确分数、总计变化、来源与守恒一致，且输入和预期不变；冻结指纹和实际运行记录见 [A3-09回归](regression_checks/A3-09.md)。不重复既有unknown变体，不把产品关联关键DQ异常混入本例或静默降级。

A3-10 固定样例 `10_missing_product_join_blocks.json` 专门覆盖关键产品关联缺失，先行Oracle及来源见 [A3-10说明](manual_checks/A3-10.md) 和 [台账](manual_checks/A3-10.json)。J10-C2引用不存在的产品复合键，其他条件合法；预期整次比较blocked_by_quality，两窗指标及变化为null，不发布类别或unknown行。它与A3-09合法产品category_id=null明确区分。现已完成参考层最小修复：缺失产品关联以ValueError拒绝，合法category_id=null仍保留；原missing=product冲突变体改为拒绝检查。真实红灯、规则更正与绿灯回归见 [A3-10回归记录](regression_checks/A3-10.md)。先行Fixture与Oracle不改，ValueError不等于生产blocked_by_quality状态映射，未宣称生产DQ已实现。

未来生产实现应独立编写，并与这些固定预期比较，不能导入本参考函数作为其业务实现，否则失去对照独立性。
