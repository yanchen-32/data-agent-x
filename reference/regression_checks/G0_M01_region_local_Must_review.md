# M01参考层：回归与局部关闭评审

日期：2026-11-13（Asia/Shanghai）。结论：**本轮回归全部通过；暂不关闭M01参考层。** 固定W/A及三维共同Scope已具备真实数值回归，但RG03.D和RG05全地区未知控制仍缺完整的事件/订单来源直接核对断言。测试通过和证据齐备分开评定，不以39项或209项的数量替代局部Must完成条件。

## 1. 依据及关闭范围

局部Must依据为[G0覆盖矩阵M01](G0_fixture_coverage.md)要求的三维固定分组、同Scope、互斥穷尽、Fraction与来源追溯，以及[region方案RG01～RG06](../manual_checks/G0_M01_region_plan.md)、[测试矩阵§5](../manual_checks/G0_M01_region_test_matrix.md)要求的支付/退款成员、事件与source_row_id逐项核对。三份历史草案及其冻结哈希不改；未知规则采用已审定的[M01-region-rules-v1](../manual_checks/G0_M01_region_rule_review.md)。

本评审只涉及公开开发样例上的独立参考计算和可复核证据。生产权限、SQL、DQ状态映射、QueryEvidence、序列化、贡献分解、正式评测及本人独立验收均不由本次pytest代替。A3-11最小渠道Must既有关闭结论不重开，C08仍为非阻塞Should。

## 2. 本轮实际运行

环境：CPython 3.10.12、pytest 9.1.1、Linux x86_64；复用既有开发虚拟环境，显式PYTHONPATH=src，未安装或修改依赖。实际安装版本另绑定FastAPI 0.141.1、Starlette 1.6.0、Pydantic 2.13.5、httpx 0.28.1、httpx2 2.13.0。

按顺序真实执行以下三阶段，全部退出0，无失败或跳过：

| 运行目录/范围 | 实际结果 | 退出码 |
| --- | --- | --- |
| 开发工作树region专项，附-rA身份 | 39 passed in 0.23s | 0 |
| 开发工作树region＋总体＋类别＋渠道＋静态Fixture | 149 passed in 0.46s | 0 |
| 隔离公开候选全量pytest | 209 passed in 0.76s | 0 |

三次范围重叠，不累计为397个独立测试。209项不是开发工作树全量，也不是已发布分支运行或CI；此前39/149、公开198及其他历史数量保留原版本，不替代本轮输出。

实际参数如下，解释器位置以PYTHON标签表示，须替换为上述既有虚拟环境解释器；为避免记录本机路径，原始输出只替换该解释器位置，其余argv和stdout保留：

```text
开发树：PYTHONPATH=src PYTHON -B -m pytest tests/test_reference_region_cohort.py -rA -o addopts= -q -p no:cacheprovider
开发树：PYTHONPATH=src PYTHON -B -m pytest tests/test_reference_region_cohort.py tests/test_reference_cohort.py tests/test_reference_category_cohort.py tests/test_reference_channel_cohort.py tests/test_boundary_fixtures.py -o addopts= -q -p no:cacheprovider
公开候选：PYTHONPATH=src PYTHON -B -m pytest -o addopts= -q -p no:cacheprovider
```

原始输出含环境、两套文件指纹、全部39条region PASSED身份、完整实际命令参数、stdout和退出码，见[G0_M01_region_local_review_pytest.txt](G0_M01_region_local_review_pytest.txt)，SHA-256为`3028a08978c098cf18e984644b48efd3608b46f6357a22d41a926663d454dbd2`。

[执行版本清单](G0_M01_region_local_review_manifest.json)SHA-256为`e849f81dfb722bac79cd9257a0dd998ccc2fb08da44fda067ebc1f6e9ac81578`，分别绑定开发和公开候选各59份计算器、测试、配置、Fixture及独立预期/规则来源。两套环境配置分别记录，不用开发pyproject指纹冒充公开版本。运行前后各自59份文件指纹均不变，当前地区测试在两树中逐字节相同。

## 3. RG01～RG06逐项评定

以下评定依据实际断言内容和本轮执行，不把“代码存在某个分支”直接登记为验证通过。

| 条目 | 已覆盖及可定位断言 | 本轮评定/剩余 |
| --- | --- | --- |
| RG01：单地区先过滤再分组 | test_region_reference_matches_frozen_oracle_and_sources[RG01.W]完整对照四行、3/1→4/3、精确率/变化、支付/退款成员及来源，排除东南来源 | 最小要求具备；不等于真实授权隔离 |
| RG02：全地区有区分力分组 | 同函数[RG02.A]对照六行和两地来源；基期NW3/1、SE2/1，当前NW4/3、SE2/1；缺席组RG02.Q五行且不补零率 | 最小数值/成员/来源要求具备；A仅是明确授权假设的合成Scope |
| RG03：退款去重、支付窗归属及零退款 | deduplicates_refunds_for_southeast_order、refund_follows_payment_window_and_region、keeps_positive_denominator_zero_refund_group均通过；D两笔事件对应一个U，T跨日历窗仍归原支付窗，Z保留Fraction(0) | **来源证据仍不完整**：D只断言目标事件数量/不同refund_id及冻结数值/退款订单结果，未直接核对新增有效事件的ID与source_row_id集合及其去重订单来源。不能将T/Z单事件来源辅助断言视为D多事件来源已覆盖 |
| RG04：目录/关键关联与比较门槛 | 两目录重复键、外域/快照六项；过滤外产品缺失ready/immature；M/P/R不足、两个等号、空基期、过滤Scope成熟差异均有真实通过结果 | 既定局部门槛已覆盖；ValueError/insufficient_evidence不替代生产blocked_by_quality |
| RG05：稳定ID、未知与过滤 | 同名两ID、label=None、两种A未知、两种W排除未知及非法过滤/null源地区均通过；同名及W排除已核对来源 | **来源证据仍不完整**：A未知两个用例目前仅断言代表性N/U/率、行数、unknown订单及当前总计，没有逐项回查未知支付/退款来源、原地区ID→unknown映射及基期不受影响的完整成员/来源。原输入哈希绑定不替代结果来源断言 |
| RG06：输入隔离/重排与三维共同Scope | input-only、前后不变、返回值污染隔离、重复/交错、A联合逆序、W/A六项单独逆序、W/A三维各自守恒均通过；region仍完整对照独立Oracle | 最小隔离和共同Scope要求具备；W联合逆序尚未执行，不声称所有重排变体都通过 |

39项构成可由本轮-rA核对：RG01/02固定2、RG03为3、返回值/联合重排隔离1、独立重排6、过滤Scope成熟1、比较不足4、两个等号2、缺席组1、产品缺失2、目录6、RG05未知2/同名1/W未知排除2/缺label1/非法3，以及三维共同Scope2。

## 4. 剩余项及下一步验收方式

### 关闭前须补齐的直接来源证据

1. **RG03.D多事件来源**：沿用现有D变体和台账，不新增框架或主例；从实际退款订单结果追溯原始两笔合格事件，逐项核对KR11-S-C-A1和KR11-RG03-S-C-SECOND、两条source_row_id、完整订单键及支付观察期；事件集合有两项，去重退款订单集合仍仅K11-S-C-A1。不能套用“一单只有一事件”的固定来源辅助函数。
2. **RG05.A合法未知来源**：沿用unknown-explicit/unknown-unregistered两项；依据先行台账对照完整双窗组/总计、成员及来源，在测试端核对原ID→unknown、支付来源r11-order-s-c-app-1及退款事件KR11-S-C-A1/来源r11-refund-s-c-app-1，当前SE剩余支付单无退款、基期不受影响。无需新增参考函数返回字段，也不以运行输出回填预期。

两项来自既有M01来源追溯要求及矩阵§5的正例共享断言，不是新增生产功能或提高样例数量门槛。现有数值正确仍可保留其“计算通过”状态，但“来源断言完整”不能据此自动判过。本轮只评审，没有编写这些补充测试，不宣称已执行。

### 非阻塞的剩余变体与范围外能力

- RG05.label-absent与RG06.W-reverse-combined仅有登记输入，未执行；前者已有label=None代表缺展示名规则，后者已有W单独逆序及A联合逆序。按本次最小参考层评审不据此扩大阻塞范围，但明确保留执行缺口，不将它们计入已通过变体。
- 其他坏格式、全维组合、未知生命周期等未穷举；矩阵允许按真实校验分支选代表，不要求全字段笛卡尔积。C08展示名继续保持原非阻塞Should，不升为关闭门槛。
- M02跨域合法正例、M03贡献、M04其他退款DQ、M05真实签收、M06生产链路、M07正式评测仍按各自Must推进；本评审不把它们并入或随M01局部一起关闭。

## 5. 冻结保护、公开候选及四类状态

| 绑定对象 | 本轮SHA-256 |
| --- | --- |
| tests/test_reference_region_cohort.py | 09a611917d87e492b8e58ea01ade88c045d3a314cd2e191ca8231297fbfafb71 |
| reference/region_cohort.py | 4652685bd2a104a047a09e62b8eb26c9aa400330fb1a2268bce4e00987c15dba |
| reference/manual_checks/G0_M01_region_expected.json | 50bca606d29077276d7a5d39c0c55dc0fbd57cfa5a0ff836db953bd9e301b1ce |
| 原11号Fixture | d652f050a45279f86b5900b76fdb1327ad9cefdaa114ad61a5d8e6457038f6f8 |
| M01-region-rules-v1文件 | 5322018b50b74da02b32c888b6777e9527fecd84b58d66b4a752ed664343c96c |

候选从本地已提交的公开树7530cb9cbde5c638ade41b918992992ff2849a7d复制至隔离临时目录，只更新当前region测试及可公开的RG05/RG06增量记录；没有纳入开发Provider、私有进度、环境同步记录或旧开发历史。原公开工作树/分支不变。候选的计算器、冻结文件与该公开父提交相同，当前测试为39项；父提交本身仍是此前28项版本，不能把本轮209项记到旧提交上。

| 状态类型 | 本轮真实状态 |
| --- | --- |
| 本地pytest | 开发39/149及隔离公开候选全量209实际通过，文件版本由上述清单分别绑定 |
| 公开交付 | 未提交、未推送；仅准备可审查的隔离候选，本轮未查询远程最新refs |
| GitHub Actions CI | 未触发或查询；公开候选本地全量不是CI |
| 用户本人独立验收/L3 | 没有取得本人验收证据，不代签、不以助手评审代替 |

本轮没有计算失败，也没有修改测试、参考实现、生产Runtime、原Fixture/expected或冻结规则；仅新增回归证据及评审记录，并追加阶段状态。结论为**回归通过，M01参考层仍开放，待上述两处来源证据补齐后再审**；G0和生产验收均不通过本轮自动放行。
