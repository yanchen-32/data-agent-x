# G0 M01：最小region参考入口与首批回归

日期：2026-11-10（Asia/Shanghai）。状态：**最小入口已实现，RG01.W四行/RG02.A六行与冻结Oracle一致，首批13项本地测试通过。** 完整RG03～RG06控制矩阵及三维共同Scope验收尚未闭环，M01/G0不关闭。

## 实现与冻结契约

新增[region_cohort.py](../region_cohort.py)的calculate_region_reference(input)，只依赖标准库与总体calculate_reference：复用原支付窗口/地区过滤后的candidate_order_ids、成熟/水位、比较状态和总体指标，从原始退款按(domain_id,snapshot_id,order_id)独立重建成功退款订单集合，同单事件去重后与各地区支付集合相交。分组直接使用订单region_id，不经过产品类别或channel分组结果，产品只提供关键关联核验。

products/regions目录按完整复合键检查唯一性和域/快照；全部原始订单关键产品关联在比较不足返回之前检查，覆盖过滤外订单。非法过滤ID不能改成[]或正常空窗。已登记地区缺label保留ID；预审合成输入中非关键未登记地区/显式哨兵进入__unknown__；真实授权、快照可信性由调用侧预审，函数不提供授权开关，也不声称验证了生产权限。

结果保留总体字段，新增aggregate_rows、group_order_ids、group_refunded_order_ids；总计在前、地区ID排序，组台账订单ID排序，候选保持总体原始顺序。计数为int、率为Fraction；比较不足时聚合行与分组台账为空，原总体两窗指标不发布。局部非法输入以ValueError拒绝，不伪造生产DQ/HTTP状态。函数无文件/网络访问，不读取expected或修改input。

[冻结Oracle](../manual_checks/G0_M01_region_expected.json)仍为v1，完整SHA-256为50bca606d29077276d7a5d39c0c55dc0fbd57cfa5a0ff836db953bd9e301b1ce；[规则审定](../manual_checks/G0_M01_region_rule_review.md)版本为M01-region-rules-v1，SHA-256为5322018b50b74da02b32c888b6777e9527fecd84b58d66b4a752ed664343c96c。原11号Fixture、原独立expected、114行人工台账、规则与矩阵原字节均不改，未按实际结果回填答案。

## 首批专项覆盖与限制

[新增测试](../../tests/test_reference_region_cohort.py)直接从冻结input及明确变更装配W/A和本轮控制，先核对既有输入指纹，再只把input传给入口。复用原渠道测试的_InputOnly通用保护类，不修改其代码或原测试；Oracle、各source文件和内存前后不变，固定其已有哈希而非重算“新基线”。候选按集合比较，冻结分数只在断言端解码为Fraction。

| 覆盖 | 本轮实际项数 | 断言与预期来源 |
| --- | --- | --- |
| RG01.W/RG02.A固定结果及来源 | 2 | 四/六行逐字段比较，精确Fraction、metrics变化、两类分组订单；原始支付/退款来源回查，互斥穷尽及ΣN/ΣU守恒，W排除SE |
| SE同单第二笔成功退款 | 1 | 使用已绑定RG03.D输入；人工台账§5 D要求事件增加但U不变，实际仍匹配原RG02.A冻结六行和退款订单集合 |
| 返回值、重复/交错Scope及联合重排隔离 | 1 | 修改旧返回值不污染重复结果，交错W/A后仍匹配冻结预期，A订单/退款/地区目录联合逆序后行/台账不变；候选仅比较集合 |
| 成熟期随过滤Scope改变 | 1 | as_of=09-19时W ready且匹配原冻结四行，A因SE尚未成熟而insufficient_evidence、所有两窗指标/分组不发布 |
| 过滤外SE订单关键产品缺失 | 2 | ready/immature均ValueError，错误包含订单ID、source_row_id和完整产品键，不能降级unknown或仅返回不足 |
| 已预审合成Scope的显式/未登记未知地区 | 2 | 人工台账§7 U：当前SE=1/0、unknown=1/1、总体6/4不变，保留来源订单；不是实际授权探针 |
| 已登记地区label=None | 1 | 先行身份不变量：仅相应label变化，地区ID、数字及台账与冻结基线相同 |
| 非法过滤或源地区坏格式 | 3 | 未登记过滤ID、哨兵过滤、订单region_id=None分别ValueError，不静默扩大Scope |

这13项不代表原40个变体都已执行或完整Oracle都已冻结。目录重复/混域、支付/退款水位负例与等号、空基期/缺席组、跨日历窗退款、所有展示名/坏格式变体、分别逆序和三维共同Scope对照等仍按矩阵后续核对。实现有相应拒绝/复用分支，不将未执行的分支写成已验收；C08仍为非阻塞Should。

## 实际命令、环境与结果

环境：开发工作树，CPython 3.10.12、pytest 9.1.1、Linux x86_64，解释器为本仓库.venv/bin/python，PYTHONPATH=src，没有安装依赖。源码和测试当前尚未提交，已知公开2fe6d51只含前阶段文档，不冒充已包含本次实现。运行版本由以下文件SHA-256绑定：

| 文件 | SHA-256 |
| --- | --- |
| reference/region_cohort.py | 4652685bd2a104a047a09e62b8eb26c9aa400330fb1a2268bce4e00987c15dba |
| tests/test_reference_region_cohort.py | f00239954ae88529d3a929f7bc4d708ba6d5d49577c9515c93fc0a6a6f0b5305 |
| [G0_M01_region_pytest.txt](G0_M01_region_pytest.txt) | cb6ad15e224447aad4de3d64bf1aad7e6946366c2bb0e1fe1212a8b04cec1873 |

实际顺序为专项、相关参考及静态、全量，命令及完整输出保存在上表原始输出文件：

| 范围 | 实际结果 | 退出码 |
| --- | --- | --- |
| region专项，附-rA逐项身份 | 13 passed in 0.18s | 0 |
| region＋总体＋类别＋渠道＋静态Fixture | 123 passed in 0.55s | 0 |
| 开发工作树全量pytest | 188 passed in 0.69s | 0 |

首次专项同为13 passed in 0.18s，随后按原始输出中的顺序复跑专项和相关，再执行全量。123项=region13+总体9+类别38+渠道42+静态21，范围重叠不相加；188为本轮实际全量输出，不从历史数量推算。无失败，无冻结答案或既有业务实现修订。

全量沿用既有API/TestClient沙箱内停滞限制，获准在沙箱外本地执行，本轮没有新增沙箱内全量失败。**全部结果均是开发工作树本地pytest，不是公开工作树、GitHub Actions CI、生产授权验证或用户本人L3/独立验收。** 开发树包含既有未公开内容，188项不能当作公开分支全量结果。

## 文件保护与阶段结论

运行前后核对全部原有测试/参考与生产文件、主Fixture/Oracle/规则/人工台账、旧输出及Provider文件哈希不变；本次新增region入口、测试及本轮记录，同步reference入口、G0阶段和架构当前行为，不修改依赖或生产Runtime。原有总体/类别/渠道测试实际无回归。

目前只确认“最小region入口与两份冻结正常预期相符，以及上述代表性控制”。三维共同Scope和完整控制矩阵仍需实际证据，再评审M01；不因新增13项或全量通过宣告G0完成。未提交或推送，不代签用户本人验收。

## RG01/RG02最小回归补强（2026-11-10）

### 复用已有测试，只补缺失断言

现有test_region_reference_matches_frozen_oracle_and_sources已按RG01.W/RG02.A参数化，覆盖单地区四行、全地区六行、冻结N/U/率、两类分组订单和守恒。本轮不新增同义测试函数，也不重建专项；保留13项收集数量，在原两项中补强以下来源检查：

- 退款索引改用(domain_id,snapshot_id,refund_id)完整键，从**实际返回的退款订单集合**回查原始事件，再与冻结的组退款事件ID和source_row_id集合比较；不再只从预期事件ID向原始数据作单向查找。
- 核对实际组支付单的原region_id及组支付来源，并将支付来源、退款事件ID和退款来源汇总后分别对照冻结整体来源集合；W额外明确排除SE支付来源、退款事件及退款来源。
- 两窗组支付/退款集合互斥穷尽、ΣN/ΣU与冻结总计及实际metrics一致；率和两项变化均显式要求Fraction，候选继续只比较集合。

来源回查仅用于RG01/RG02已冻结正常input，没有在测试中另写成功状态/观察期计算来生成Oracle，也不把固定正常样例的来源断言直接用于新增退款事件控制。input-only保护、固定哈希、调用前后内存及文件不变检查沿用已有机制，冻结expected没有改动。

### 本轮实际执行与版本

环境：开发工作树、CPython 3.10.12、pytest 9.1.1、Linux x86_64，解释器为本仓库.venv/bin/python，显式PYTHONPATH=src。完整命令及stdout保存在[G0_M01_region_RG01_RG02_pytest.txt](G0_M01_region_RG01_RG02_pytest.txt)，SHA-256为`7fcce42dfdf20a90d985ebdc792ee2174352bd419837c3d3bd46fa6d126c54d5`。

| 实际范围 | 实际结果 | 退出码 |
| --- | --- | --- |
| 地区文件，-k matches_frozen_oracle_and_sources -rA | 2 passed, 11 deselected in 0.15s | 0 |
| 地区专项整个文件 | 13 passed in 0.18s | 0 |
| 原tests/test_reference_cohort.py | 9 passed in 0.03s | 0 |

修改后首次定向也为2 passed, 11 deselected in 0.15s；随后按表中三条命令执行并归档。原总体9项实际运行无失败；RG01/RG02两项属于地区13项子集，不能将三次运行计为24个独立测试。专项原有其他代表性控制也在本轮13项范围内执行，但不是40个变体或完整矩阵均通过。

当前地区测试SHA-256为`46706e3d95600b25a75198e6aada7d6ecb8e262a27d6e5c8882c07c3b75ac6f9`；地区实现仍为4652685bd2a104a047a09e62b8eb26c9aa400330fb1a2268bce4e00987c15dba，冻结Oracle仍为50bca606d29077276d7a5d39c0c55dc0fbd57cfa5a0ff836db953bd9e301b1ce。上文f0023995测试版本、旧原始输出及188项全量保留其此前阶段，不冒充当前断言版本已跑全量。

本轮仅补强地区测试、追加本节和新增执行输出；参考/生产代码、原Fixture/expected、台账/规则/矩阵、既有总体测试及旧证据均不修改。没有失败或为实现输出调整预期。本轮未运行全量、类别/渠道组合或公开工作树pytest，未查询CI，未提交/推送；全部是本地执行证据，不是GitHub Actions CI或用户本人L3。测试矩阵仍是计划，实际覆盖以上述真实输出和测试断言为准；M01/G0保持开放，C08仍是非阻塞Should。

## region实现公开交付验证（2026-11-10）

以上保留各开发阶段及旧输出对应版本；本次公开候选工作树已实际通过地区13项、相关123项、全量183项，详见[公开交付记录](G0_M01_region_implementation_publication.md)和公开版本清单。规则/冻结Oracle/region入口/当前断言版本随本次追加交付，原Fixture及既有计算器不变。M01/G0仍开放、C08非阻塞；公开本地pytest不是CI、真实授权或本人验收。
