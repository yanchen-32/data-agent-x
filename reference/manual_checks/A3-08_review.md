# A3-08 新增与退出类别：独立数值台账

日期：2026-10-23。复用已有 [08_category_entry_exit.json](../../tests/fixtures/order_boundaries/08_category_entry_exit.v1.json) 初稿，不覆盖、不重复创建同名样例。本轮补齐单独的 [手填JSON台账](A3-08_review.json)，先查看input逐单填写，再对照既有静态答案和参考计算。已有 [Oracle逐单推导](../../tests/fixtures/order_boundaries/ORACLE.md) 与 [计算回归记录](../regression_checks/A3-08.md) 保留原样。

同一会话此前已知目标数值，故这是输入驱动、独立于程序输出的数值台账，不声称首次盲审、第二位独立人工审核或用户签字验收。台账中的N/U/率先静态填写，未从参考函数、SQL或生产代码生成；JSON序列化及hash不承担业务计算。

2026-10-26版本定位说明：本文数值与历史输出只对应v1。原文件已逐字节另存为 `08_category_entry_exit.v1.json`，上述链接及复现代码仅修正到该历史定位；冻结JSON台账中的原始路径字段保留原文，其SHA-256仍指向v1。当前主文件已升级v2，不与本文数值混用。

## 固定输入与关联

- 域/快照：`(domain_a,fixture_category_entry_exit)`；地区过滤为空。
- 基期：`[2026-09-01T00:00:00Z,2026-09-08T00:00:00Z)`；当前：`[2026-09-08T00:00:00Z,2026-09-15T00:00:00Z)`。
- H=604800秒，即7天；as_of及退款水位均为09-23 00:00 UTC，支付水位09-15 00:00 UTC。
- 产品目录在同一域/快照内保留product_a→category_a、product_b→category_b、product_c→category_c三条唯一关联。订单按完整产品复合键关联，退款按完整订单复合键关联。三个类别在目录中均存在，不用目录行的存在与否判断跨窗新增/退出。

Fixture SHA-256：`b2ffe9d156a9e010f28bbfda072589c95b8ee8dd426f98a0da8c1515ed0cb580`。input按 `ensure_ascii=False,sort_keys=True,separators=(',',':')` 序列化后UTF-8字节的SHA-256：`3f31f3a1ec845747f98e5c53b0dca065bc761ae1167fe69d88b63fc8e4d3d856`。

## 逐订单手工依据

下表日期均为2026年UTC的00:00；六单支付有效性均为True。完整来源行和产品ID见JSON台账。

| 来源行 | 订单 | 类别ID | 支付 / 成熟日 | 支付窗 | 合格退款 |
| --- | --- | --- | --- | --- | --- |
| r08-row-a-b1 | E-A-B1 | category_a | 09-02 / 09-09 | 基期 | 无 |
| r08-row-b-b1 | E-B-B1 | category_b | 09-03 / 09-10 | 基期 | r08-refund-b-b1 / ER-B-B1，09-05成功 |
| r08-row-a-c1 | E-A-C1 | category_a | 09-09 / 09-16 | 当前 | r08-refund-a-c1 / ER-A-C1，09-11成功 |
| r08-row-a-c2 | E-A-C2 | category_a | 09-10 / 09-17 | 当前 | 无 |
| r08-row-c-c1 | E-C-C1 | category_c | 09-11 / 09-18 | 当前 | 无 |
| r08-row-c-c2 | E-C-C2 | category_c | 09-12 / 09-19 | 当前 | 无 |

ER-B-B1落在E-B-B1的闭合观察期[09-03,09-10]内；ER-A-C1落在E-A-C1的[09-09,09-16]内，两笔均为success且不晚于as_of。其余四单在完整退款表中均没有关联事件。因此基期退款订单集合为 `{E-B-B1}`，当前为 `{E-A-C1}`，不将退款事件数直接当作一般情况下的分子。

## 先行静态数值

| 类别 / 身份 | 基期支付 / 退款订单 | 基期N、U、率 | 当前支付 / 退款订单 | 当前N、U、率 |
| --- | --- | --- | --- | --- |
| A / shared | {E-A-B1} / {} | 1、0、0 | {E-A-C1,E-A-C2} / {E-A-C1} | 2、1、1/2 |
| B / exit | {E-B-B1} / {E-B-B1} | 1、1、1 | 缺席，无聚合行 | 不适用，不补率 |
| C / entry | 缺席，无聚合行 | 不适用，不补率 | {E-C-C1,E-C-C2} / {} | 2、0、0 |
| 总计 | {E-A-B1,E-B-B1} / {E-B-B1} | 2、1、1/2 | 四单 / {E-A-C1} | 4、1、1/4 |

按稳定类别ID，基期S0={A,B}、当前S1={A,C}，故shared=S0∩S1={A}，exit=S0−S1={B}，entry=S1−S0={C}。这是支付集合的跨窗身份，不代表类别永久上线或下线。

每单恰好关联一个产品及一个类别，组间无交集且没有遗漏。基期ΣN=1+1=2、ΣU=0+1=1；当前ΣN=2+2=4、ΣU=1+0=1。总体率按总U/总N核算，不相加或平均各组率。总体绝对变化为1/4−1/2=−1/4，相对变化为−1/2；两窗总体N都大于0。

当前B、基期C不生成聚合行或空组台账，更不能伪造零分母退款率。当前C是真实N=2、U=0，率应为0。所有订单最晚于09-19成熟，早于as_of及退款水位；支付水位覆盖两窗末端，故人工判断 outcome=ready。

## 保存后对照

手填JSON台账先行保存后的SHA-256为 `e6e0f2408aa31082232e7e8ccb74ecb48b76e06bdaced8266c790a96c97ddd3b`。保存后才读取既有静态预期，并调用 `calculate_category_reference(fixture["input"])`；计算函数不接收台账或 `expected`。对照程序在函数外用 `Fraction` 比较六行结果、两种归组台账、候选队列、三类身份、成熟水位、总体变化与守恒关系。

实际输出：

```text
0 None 2 1 1/2
0 category_a 1 0 0
0 category_b 1 1 1
1 None 4 1 1/4
1 category_a 2 1 1/2
1 category_c 2 0 0
手填台账、既有静态预期与参考输出的六行结果一致。
shared=A；exit=B；entry=C；两窗N/U守恒、缺席组无行、来源台账一致。
```

最小复现方式（仅比较已保存的手填值，不生成答案）：

```python
import json
from pathlib import Path
from fractions import Fraction
from reference.category_cohort import calculate_category_reference

fixture = json.loads(Path("tests/fixtures/order_boundaries/08_category_entry_exit.v1.json").read_text(encoding="utf-8"))
manual = json.loads(Path("reference/manual_checks/A3-08_review.json").read_text(encoding="utf-8"))
actual = calculate_category_reference(fixture["input"])
wanted = [{**{k: v for k, v in row.items() if k != "rate_fraction"},
           "rate": Fraction(row["rate_fraction"])} for row in manual["aggregate_rows"]]
assert actual["aggregate_rows"] == wanted
assert actual["group_order_ids"] == manual["group_order_ids"]
assert actual["group_refunded_order_ids"] == manual["group_refunded_order_ids"]
```

相关回归命令及实际输出：

```bash
.venv/bin/python -B -m pytest tests/test_reference_category_cohort.py tests/test_reference_cohort.py tests/test_boundary_fixtures.py -o addopts='' -q -p no:cacheprovider
```

```text
.....................................................                    [100%]
53 passed in 0.16s
```

53项包含30项分组回归、9项总体参考回归及14项静态Fixture检查，已含A3-08的3项专门计算回归。本轮未重跑全量pytest，不将先前118项通过写作本轮全量结果。

没有差异需要改写输入、既有预期或参考实现。本轮仅新增本说明和独立JSON台账；原Fixture、公共Oracle、参考实现、既有测试和Provider在操作前后SHA-256均未变化。`git diff --check` 通过。没有新增计算框架，没有计算within/structure/entry/exit贡献数值，也未宣称生产SQL或正式调查系统已验收。文件仍为待用户独立人工验收的初稿，本轮不提交或推送。
