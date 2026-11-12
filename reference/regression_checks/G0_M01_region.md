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

## RG03.T/Z：退款归属与合法零退款（2026-11-12）

### 既有覆盖、独立依据及输入

实施前地区测试已有RG03.D同单多事件去重，未包含RG03.T/Z；本次仅补T/Z及其变体重放，不重复D。退款资格、地区和窗口归属沿用[人工台账§3/5](../manual_checks/G0_M01_region_expected_draft.md)及[矩阵RG03.T/Z](../manual_checks/G0_M01_region_test_matrix.md)，不从参考函数输出生成答案。

两个控制均基于RG02.A的深拷贝，沿用固定域/快照和原两地区输入；假定合成主体已获全地区授权，不是生产权限验证。已有JSON登记的两项精确变更及规范化输入SHA-256如下，测试重放后先核对该指纹，再仅传input给calculate_region_reference：

| 控制 | 已登记的唯一变更 | input SHA-256 |
| --- | --- | --- |
| RG03.T | KR11-S-B-W1.refund_at由09-06改为2026-09-09T00:00:00Z | 503a4d242de946e57a4eeb5d562c9c0660c506cd6e07ff127f7ffe24236e9251 |
| RG03.Z | 移除KR11-S-B-W1事件，保留两笔SE基期支付 | 0c5a36c701b45be6e4fa58cfa6d0fde4127fe322db6e6d084338700ee2190d90 |

T的订单K11-S-B-W1在09-05支付、09-12成熟；09-09退款落在当前日历窗，但仍位于该支付订单的闭合7天观察期且不晚于as_of，必须计入基期东南。事件ID及来源r11-refund-s-b-web-1不变。Z仅移除该事件，不能删除对应支付、丢弃零退款组或触发空基期阻断。

### 六行独立预期及来源断言

以下数值直接取先行台账§4/5，NW=region_northwest、SE=region_southeast。T全部复用RG02.A六行冻结输出；Z在测试端对冻结预期的深拷贝作台账明确的静态修订，不写回任何expected文件。

| 窗口/行 | T：N/U/率 | Z：N/U/率 |
| --- | --- | --- |
| 基期总计 | 5/2，2/5 | 5/1，1/5 |
| 基期NW | 3/1，1/3 | 3/1，1/3 |
| 基期SE | 2/1，1/2 | 2/0，0 |
| 当前总计 | 6/4，2/3 | 6/4，2/3 |
| 当前NW | 4/3，3/4 | 4/3，3/4 |
| 当前SE | 2/1，1/2 | 2/1，1/2 |

两者均ready。T总体绝对变化4/15、相对变化2/3；Z绝对变化2/3−1/5=7/15、相对变化(7/15)/(1/5)=7/3。所有率及变化均要求精确Fraction；Z基期SE明确为Fraction(0)，不是None或浮点0。

T的两窗支付/退款订单集合、来源和全部输出仍匹配冻结A。Z支付集合不变：基期SE仍为{K11-S-B-A1,K11-S-B-W1}，退款集合为空；基期整体退款集合仅剩{K11-N-B-A1}；其他组及当前退款集合不变。T/Z均回查完整(domain_id,snapshot_id,order_id)支付关联和原始退款来源，与冻结组来源或台账明确移除后的集合核对。Z基期SE事件ID/来源集合为空，不把事件发生时间当成支付窗口。

两项分别检查六条行及所有输出字段、组支付/退款成员唯一且互斥、候选集合穷尽、退款集合从属支付集合、每组N/U与成员数一致、各组ΣN/ΣU与总体一致。输入保护复用_InputOnly、调用前后深拷贝及既有region_fixture磁盘/内存保护；不重写已有输入保护测试。

### 实际执行与版本绑定

环境：本地开发工作树，解释器.venv/bin/python，CPython 3.10.12、pytest 9.1.1、Linux x86_64，PYTHONPATH=src；未安装依赖。原始命令、版本、源码指纹、完整stdout和退出码保存在[G0_M01_region_RG03_T_Z_pytest.txt](G0_M01_region_RG03_T_Z_pytest.txt)，SHA-256为`4f146e2165726d131cfb5431636cfd977fa513bf675d4cd9f6e61ccd0e4e8c57`。

| 实际范围 | 实际结果 | 退出码 |
| --- | --- | --- |
| 地区文件-k两项新函数名，附-rA身份 | 2 passed, 13 deselected in 0.25s | 0 |
| 地区专项整个文件 | 15 passed in 0.20s | 0 |
| 地区＋总体＋类别＋渠道＋静态Fixture | 125 passed in 0.61s | 0 |

三次范围重叠，不累加为独立测试数量。没有失败或预期修订；125项是本轮实际结果，包含既有地区13项及其他相关回归，不是推算。未执行全量pytest或公开工作树测试，未查询GitHub Actions；本轮是开发工作树本地执行，不是CI或用户本人L3验收，尚未提交/推送。

| 本轮绑定对象 | SHA-256 |
| --- | --- |
| tests/test_reference_region_cohort.py | 9feb57de18645b1a2e791942e67a89bc55d5f816835a9a189c5da55d591dcd31 |
| reference/region_cohort.py（不变） | 4652685bd2a104a047a09e62b8eb26c9aa400330fb1a2268bce4e00987c15dba |
| 冻结region JSON（不变） | 50bca606d29077276d7a5d39c0c55dc0fbd57cfa5a0ff836db953bd9e301b1ce |
| 原人工台账（不变） | 99040571560c27f8eadd84ce72ee4640a53f25a6eadfaff8ffd6ba4705fc9fe3 |
| 原11号Fixture（不变） | d652f050a45279f86b5900b76fdb1327ad9cefdaa114ad61a5d8e6457038f6f8 |

冻结JSON仍仅有RG01/RG02完整expected；其余变体指纹不等于完整业务输出均已冻结。本轮T/Z的独立答案来自既有台账并落实为测试断言，未扩大JSON冻结范围或改写历史执行证据。参考/生产实现、原Fixture/expected、旧测试及Provider保持原状。RG03.D/T/Z现均有真实地区回归；其余控制及三维共同Scope仍按矩阵推进，M01整体/G0保持开放，C08仍为非阻塞Should。

## RG04：目录复合键拒绝（2026-11-12）

### 缺口与先行拒绝规则

实施前region入口已有关键产品缺失ready/immature两项控制，没有regions/products目录重复或外域/外快照的直接测试。既有渠道C04提供设计范式，不证明region入口已验证。本轮复用[矩阵§3](../manual_checks/G0_M01_region_test_matrix.md)已登记的六个单故障变体，只新增region依赖的两个目录控制，不复制channels目录、扩展地区目标组合或修改既有类别/渠道测试。

独立拒绝依据为DD02 §1、目录完整复合键契约及[规则RR07](../manual_checks/G0_M01_region_rule_review.md)：目录重复键不能由字典覆盖；域/快照不一致行不能凭相同局部ID混入或被忽略；地区过滤不能豁免原始目录核验。六项在执行前已有明确ValueError预期，不从函数输出反推规则。

### 输入、断言和来源

各项基于RG01.W深拷贝，保持西北过滤、时间、水位、订单、退款及原合法目录行不变，仅追加一条登记故障行。_variant新增append_catalog重放，逐项核对冻结JSON原有input_sha256，再通过_InputOnly只传input调用入口。没有改写原Fixture、冻结JSON或登记的变体指纹。

| 变体 | 故障行/来源 | 应拒绝的完整键 |
| --- | --- | --- |
| RG04.duplicate-regions | r11-rg04-region-dup，复制SE地区 | (domain_a,fixture_single_region_channel_v1_draft,region_southeast)重复 |
| RG04.duplicate-products | r11-rg04-product-dup，复制共享产品 | (domain_a,fixture_single_region_channel_v1_draft,product_book)重复 |
| RG04.foreign-regions-domain_id | r11-rg04-regions-domain_id | (domain_foreign_rg04,fixture_single_region_channel_v1_draft,region_southeast) |
| RG04.foreign-regions-snapshot_id | r11-rg04-regions-snapshot_id | (domain_a,snapshot_foreign_rg04,region_southeast) |
| RG04.foreign-products-domain_id | r11-rg04-products-domain_id | (domain_foreign_rg04,fixture_single_region_channel_v1_draft,product_book) |
| RG04.foreign-products-snapshot_id | r11-rg04-products-snapshot_id | (domain_a,snapshot_foreign_rg04,product_book) |

重复键两项先断言同完整键恰有两行、来源不同，再要求ValueError包含“重复目录主键”、对应region_id/product_id及完整键repr。外Scope四项先核对合法同ID行仍在、只改变指定Scope字段、另一Scope字段不变、来源不同，所有完整键仍唯一；要求ValueError包含域/快照不一致原因、目录字段和故障完整键。这样外Scope测试不会因意外重复完整键而通过，也不能按裸ID覆盖或忽略新增行。

三项regions故障均使用region_southeast，显式断言其不在西北过滤列表中，证明过滤外地区目录仍核验。products使用原共享product_book，是本入口实际依赖的目录，不虚构过滤外专属产品。所有抛错路径复用_calculate的finally断言核对input不变；fixture继续保护冻结文件及内存。ValueError是参考层拒绝，不表示生产DQ状态映射或真实权限已实现。

### 实际执行及文件版本

环境：本地开发工作树，.venv/bin/python，CPython 3.10.12、pytest 9.1.1、Linux x86_64，PYTHONPATH=src；未安装依赖。完整命令、逐项测试身份、stdout、退出码及运行文件指纹见[G0_M01_region_RG04_catalog_pytest.txt](G0_M01_region_RG04_catalog_pytest.txt)，SHA-256为`949e9ad0f52d8f3a8bef972fb2ab719adf10c4030b69e594f9118be1205d96ee`。

| 实际范围 | 实际结果 | 退出码 |
| --- | --- | --- |
| 地区文件-k两项目录函数，附-rA | 6 passed, 15 deselected in 0.19s | 0 |
| 地区专项整个文件 | 21 passed in 0.23s | 0 |
| 地区＋总体＋类别＋渠道＋静态Fixture | 131 passed in 0.59s | 0 |

测试范围重叠，不相加计数。六项均实际通过，既有RG03.T/Z、地区其他测试及总体/类别/渠道/静态测试实际无回归；本轮没有失败或预期修订。未执行全量pytest或公开工作树测试，未查询CI。本轮未提交/推送，不将本地结果记作GitHub Actions CI、生产授权验收或用户本人L3。

当前地区测试SHA-256为`cd6f899e24f87a7ea82c022d81581da85b68b5bd7333326a2639a750beb5e199`；地区实现仍为`4652685bd2a104a047a09e62b8eb26c9aa400330fb1a2268bce4e00987c15dba`，冻结Oracle仍为`50bca606d29077276d7a5d39c0c55dc0fbd57cfa5a0ff836db953bd9e301b1ce`。参考及生产代码、其他测试、Provider、原Fixture/expected、规则/矩阵和既有证据保持原字节；本次只修改地区测试、追加本节、新增原始输出。此处完成RG04目录控制，不表示RG04成熟水位等所有控制或三维共同Scope已闭环，M01/G0仍开放，C08保持非阻塞Should。

## RG04：全地区比较门槛与缺席组（2026-11-12）

### 复用登记变体和先行独立预期

此前已有RG04.scope-W/A的Scope成熟差异及目录/关键关联拒绝测试，但全地区A的单独支付/退款水位不足、成熟/退款水位等号、空基期和缺席组尚无直接控制。本次只补7项，沿用[人工台账§6](../manual_checks/G0_M01_region_expected_draft.md)及[矩阵§3](../manual_checks/G0_M01_region_test_matrix.md)的独立答案；缺席组沿用原编号RG02.Q，不改成新的RG04编号。

所有输入来自冻结JSON既有变体：RG04.M-minus、P-minus、R-minus、M-equal、R-equal、E及RG02.Q。_variant在原input深拷贝上只重放已登记变更，并核对每项原有input_sha256；不添加新变体、不改原Fixture/expected或参考实现。全地区过滤列表为[]，沿用“合成主体假定已获两地区授权”的测试前提，不表示生产权限已核验。

独立边界：A两窗最大end为2026-09-15T00:00:00Z，最晚订单成熟为2026-09-21T00:00:00Z；W的09-19成熟常量不能当作A的等号。每个不足控制单独变更一个条件，不叠加故障。

| 既有变体 | 唯一变更 | 独立预期及实际断言 |
| --- | --- | --- |
| RG04.M-minus | as_of=09-20T23:59:59.999999Z | insufficient_evidence；唯一原因观察期未成熟；仅all_orders_mature=false |
| RG04.P-minus | payments_through=09-14T23:59:59.999999Z | insufficient_evidence；唯一原因支付水位不足；仅payments_watermark_covered=false |
| RG04.R-minus | refunds_through=09-20T23:59:59.999999Z | insufficient_evidence；唯一原因退款水位不足；仅refunds_watermark_covered=false |
| RG04.E | 五笔基期支付均is_payment_valid=False | insufficient_evidence；唯一原因支付窗口无有效样本；三个quality标志均true |
| RG04.M-equal | as_of=09-21T00:00:00Z | ready、reasons=[]，三个quality均true，完整输出与RG02.A六行一致 |
| RG04.R-equal | refunds_through=09-21T00:00:00Z | ready、reasons=[]，三个quality均true，完整输出与RG02.A六行一致 |
| RG02.Q | 只停用两笔SE基期支付 | ready；基期只输出NW和总计，当前仍输出NW/SE及总计，共五行，缺席组不补行 |

所有时间均为2026年UTC。支付水位等号09-15已由原A正常样例覆盖；本轮两个等号控制也保持该值并明确核对等于当前窗口end，不新增同输入同义正例。两个等号控制均比较六条聚合行、精确Fraction、变化、支付/退款集合和来源守恒。

### 发布抑制与候选诊断分离

M−/P−/R−/E逐项要求两窗metrics的N/U/rate及absolute_change_ratio/relative_change全部None，aggregate_rows=[]，group_order_ids和group_refunded_order_ids均={}；不能只压制异常窗口而发布另一窗。明确核对唯一原因及全部三个quality标志，不以ValueError代替比较不足。

M−/P−/R−的候选仍是原A基期五单、当前六单，不能静默删除未成熟订单后发布；E的基期候选为空、当前仍是原六单。E另核对无效支付集合恰为原基期五单，防止只关闭西北三单后误称全地区空基期。候选只作为诊断集合核验，不要求函数返回不存在的诊断N/U字段，也不将其当作发布指标。

Q仅停用K11-S-B-W1和K11-S-B-A1两笔SE基期支付，原始退款事件KR11-S-B-W1仍保留，不构造孤立退款。基期总计及NW均N=3/U=1/率1/3，SE基期在聚合行、支付及退款分组台账中均不输出；当前NW=4/3、SE=2/1，总计6/4/率2/3，绝对变化1/3、相对变化1。测试端仅依先行台账对A冻结预期的深拷贝静态移除缺席组、调整基期总计及变化；全部输出、精确Fraction、来源和ΣN/ΣU守恒与该先行答案比较，不由实际结果生成答案或写回文件。

Q不是空基期E，也不是RG03.Z的正分母零退款组：前者无支付、不输出组；Z仍有两笔支付，应保留率Fraction(0)。既有RG03.Z与本轮Q同时在地区专项执行，明确区分两者。

### 实际执行和证据

环境：本地开发工作树，解释器.venv/bin/python，CPython 3.10.12、pytest 9.1.1、Linux x86_64，PYTHONPATH=src；未安装依赖。命令、逐项身份、stdout、退出码和运行文件指纹保存于[G0_M01_region_RG04_gates_pytest.txt](G0_M01_region_RG04_gates_pytest.txt)，SHA-256为`ddb29751ad594fe842fa6c190121586cc4f0e8e42164c05bb46004e312c65624`。

| 实际范围 | 实际结果 | 退出码 |
| --- | --- | --- |
| 地区文件-k新增三项函数，附-rA | 7 passed, 21 deselected in 0.20s | 0 |
| 地区专项整个文件 | 28 passed in 0.27s | 0 |
| 地区＋总体＋类别＋渠道＋静态Fixture | 138 passed in 0.61s | 0 |

范围重叠，不累加计数。没有失败或按实现修改预期；原地区及总体/类别/渠道/静态测试无回归。本轮未执行全量pytest、公开工作树测试或GitHub Actions，不冒称CI、生产DQ状态验收或用户本人L3，未提交/推送。

当前地区测试SHA-256为`f2f9fbeddd4d9f0a5f0bd8a0752401ebaaff5a208583010f2e0a182733acc963`；地区实现、冻结JSON仍分别为`4652685bd2a104a047a09e62b8eb26c9aa400330fb1a2268bce4e00987c15dba`、`50bca606d29077276d7a5d39c0c55dc0fbd57cfa5a0ff836db953bd9e301b1ce`。输入/Oracle保护沿用已有fixture及_InputOnly机制，前后核对磁盘字节和内存不变；其他原文件及旧执行证据保持原字节。

本轮只修改地区测试、追加本节和新增执行输出；没有扩大冻结JSON中完整expected的范围，没有更新生产Runtime。其余身份/输入隔离及三维共同Scope仍须按矩阵核对，M01整体/G0继续开放，C08仍是非阻塞Should。

## region控制公开交付验证（2026-11-12）

以上保留各开发阶段的源码版本、执行范围及当时未公开状态。本次公开候选已实际通过地区28项、相关138项和全量198项，详见[公开交付记录](G0_M01_region_controls_publication.md)、[原始输出](G0_M01_region_controls_public_pytest.txt)及[版本清单](G0_M01_region_controls_public_manifest.json)。新增15项与原13项均通过；原冻结文件和计算器不改。公开候选本地pytest不是CI、本人验收或生产DQ实现；M01/G0仍开放，C08非阻塞。公开交付以最终提交及远程refs核验为准。
