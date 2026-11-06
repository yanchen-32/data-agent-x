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

## A3-11冻结阶段（2026-11-02）

A3-11新增固定开发样例[单地区渠道分组](../tests/fixtures/order_boundaries/11_single_region_channel_grouping.json)。已先按原始输入复核并保存[独立expected](manual_checks/A3-11_expected.json)，冻结西北地区两个渠道和总计的六行、精确Fraction、来源集合及漏过滤反例；input与原草案相同，旧草案/初稿原字节保留，未发现数值或来源差异。冻结指纹、审核限制及实际21项静态pytest见[冻结审核记录](manual_checks/A3-11_freeze_review.md)。这只完成先行Oracle，当前category_cohort.py仍仅做类别分组；独立渠道计算及实际计算回归尚待实现，不宣称用户本人验收或G0通过。

## A3-11渠道计算及C01/C02（2026-11-03）

上节保存冻结阶段状态。现已新增[channel_cohort.py](channel_cohort.py)中的calculate_channel_reference(input)，只依赖标准库与总体参考函数：复用固定Scope的支付队列、成熟水位、总体指标和比较门槛，独立扫描原始退款并按订单去重，然后直接按订单channel_id分组。完整产品关联、目录重复/域快照检查位于不足返回之前；最小版本支持已登记渠道，未知渠道拒绝仅表示参考输入范围限制，不是业务关键DQ规则。未修改总体/类别函数或生产Runtime。

[渠道固定测试](../tests/test_reference_channel_cohort.py)绑定原有Fixture、独立expected、规范化input及expected四项指纹；C01比较四条渠道行、两条总计行、精确Fraction及总体变化，C02按基期/当前核对复合键、支付/退款来源、东南排除、分组互斥穷尽及N/U守恒。只传input，测试结束检查内存和磁盘不变，不从actual生成预期。实际专项3项、相关71项、开发全量136项通过，见[本轮运行记录](regression_checks/A3-11_channel.md)。C03～C07控制变体及C08展示名补强仍待后续，不能因固定正例通过宣称全部渠道边界或G0通过。

## A3-11 C03全地区控制（2026-11-05）

在冻结input深拷贝上只将filters.region_ids设为[]，作为另行假定已授权的全地区合成Scope。新增C03直接调用既有渠道函数，与先行unfiltered_counterexample比较双窗两渠道N/U/精确率、总体变化、增加的东南订单/退款及来源，并同时核对西北和全地区的互斥穷尽、N/U守恒；全地区调用前后的西北六行保持一致。原冻结文件与渠道实现不改，当前渠道套件4项、相关72项实际通过，原始输出见[C03测试输出](regression_checks/A3-11_C03_pytest.txt)，覆盖边界见[追加回归记录](regression_checks/A3-11_channel.md)。C04～C07及C08仍待后续，本次不是授权实现或用户L3验收。

## A3-11 C04关键关联控制（2026-11-05）

新增14项参数化/兼容检查：产品、地区、渠道目录重复键3项，保留本地合法行并混入域/快照不同但局部ID相同的目录行6项，西北/东南目标订单产品缺失×ready/immature四项，以及产品实体存在但category_id=None的合法未知兼容一项。关键产品缺失须抛包含订单ID、来源行、完整产品复合键的ValueError，东南目标已确认不在候选队列中，不能因地区过滤或未成熟而绕过。

合法非关键类别未知仍返回原渠道六行；原类别未知回归继续运行，未知channel_id的参考范围限制不提升为关键DQ规则。只补测试断言，没有修改渠道/总体/类别函数或冻结答案。C04定向14项、渠道套件18项及相关86项实际通过，原始输出见[C04测试输出](regression_checks/A3-11_C04_pytest.txt)，拒绝范围及限制见[回归记录](regression_checks/A3-11_channel.md)。C05～C07及C08仍待后续，不据这些局部参考测试声称生产DQ或G0通过。

## A3-11 C05比较前提与零退款（2026-11-05）

先按DD02和原始逐单记录保存[C05独立预期](manual_checks/A3-11_C05_expected.json)及[推导说明](manual_checks/A3-11_C05_expected.md)，再新增8项测试：仅未成熟、仅支付水位不足、仅退款水位不足、仅空基期四项不足控制，三个等号允许控制和一个合法基期零退款正例。四种不足均不发布两窗指标/变化或聚合行；N>0/U=0应ready，基期率0只使相对变化null。当前渠道26项、相关94项实际通过，[输出](regression_checks/A3-11_C05_pytest.txt)及[回归记录](regression_checks/A3-11_channel.md)保留真实证据；原Fixture/expected和参考实现不改，C06/C07及C08仍待后续。

## A3-11 C06退款去重及观察期（2026-11-05）

已核对发布方案的C06定义和哈希，只补四类追加事件在基期/当前的缺失控制，共8项：同单第二笔有效success、failed、H后1微秒、as_of后1微秒。[独立事件清单](manual_checks/A3-11_C06_expected.json)和[依据](manual_checks/A3-11_C06_expected.md)先于测试保存；所有控制复用原冻结六行、分组订单和总体变化，未生成或回填新答案。后一个场景同时在H后，按方案披露其不能孤立验证as_of，不改变编号或范围。

当前C06定向8项、渠道34项、相关102项实际通过，C01～C05保持原断言，输出见[C06执行证据](regression_checks/A3-11_C06_pytest.txt)，详细状态见[回归记录](regression_checks/A3-11_channel.md)。三种参考实现、原Fixture/expected及已发布方案均不改；C07与C08仍待后续，本地运行不代表CI、用户L3或生产验收。

## A3-11 C07输入隔离与重排（2026-11-06）

复用既有_InputOnly及channel_fixture的禁止expected访问、冻结哈希和内存/文件保护，只新增两项缺失控制：重复调用、修改旧返回值及交错全地区Scope后结果仍隔离；逆序订单、退款和全部目录后，六条聚合行与两类分组台账不变，总体候选按集合比较。原C01～C06及保护辅助代码保留，不重复实现冻结保护或生成新预期。C07定向2项、渠道36项、相关104项实际通过，见[执行输出](regression_checks/A3-11_C07_pytest.txt)及[回归记录](regression_checks/A3-11_channel.md)。C08仍待后续；本轮没有全量、公开工作树或CI执行，未提交或推送。

## A3-11 C07分别逆序与重复执行补强（2026-11-06）

将已有联合逆序测试扩为7个参数：订单、退款、产品、类别、渠道、地区分别逆序及全部联合逆序；原有返回值隔离测试不变。冻结产品/类别目录各仅一行，因此只在相应深拷贝控制中追加合法、未引用的目录项，先检查追加不影响结果，再执行有实质变化的逆序。各参数均按原始→重排→重复重排→原始调用，核对六行身份/N/U/Fraction、两类分组台账和候选集合，不要求候选列表顺序一致。C07现共8项、渠道42项、相关110项实际通过，见[新执行证据](regression_checks/A3-11_C07_reordering_pytest.txt)和[回归记录](regression_checks/A3-11_channel.md)；旧记录保留原阶段数量，主冻结数据及参考实现不变，未运行全量或CI，未提交或推送。

## A3-11最小渠道参考Must关闭（2026-11-06）

本轮按顺序实际执行渠道42项、相关110项、开发工作树全量175项，均退出码0；冻结指纹及47份源码/输入/规则/配置文件前后不变。[Must逐项评审](regression_checks/A3-11_Must_review.md)按C01～C07登记42项真实通过身份，关闭本地A3-11最小渠道参考Must；[原始输出](regression_checks/A3-11_full_regression_pytest.txt)与[公开版本摘要](regression_checks/A3-11_full_regression_public_manifest.json)保留历史开发绑定并另行记录公开复跑；原完整开发清单留在本地，历史C07当时尚未提交，已公开91e215d不冒充包含C07。C08仍为Should，G0 M01整体及其他缺口、用户本人验收保持开放；此次未提交/推送，未运行公开工作树或CI。

## 后续公开交付验证（2026-11-06）

以上保留开发阶段范围与状态；本次已在公开候选工作树实际通过渠道42项、相关110项、全量170项，源码与冻结指纹不变，见[公开交付验证](regression_checks/A3-11_C07_publication.md)。C07及本评审随此次公开追加提交交付；公开版本摘要绑定45份运行文件，完整内部开发清单保留本地。本地公开pytest仍不是CI或本人验收，仅关闭A3-11最小渠道参考Must，G0与C08保持原边界。
