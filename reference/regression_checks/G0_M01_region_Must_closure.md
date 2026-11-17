# M01：最小三维参考层Must关闭评审

公开交付版日期：2026-11-17。以下基于2026-11-16本地关闭评审选编；本地完整版原字节保留，本文件不冒充其逐字副本。
日期：2026-11-16（Asia/Shanghai）。结论：**RG01～RG06的局部必需能力均有直接代码断言及本轮实际通过记录，关闭本地M01最小参考层Must。** 此结论只覆盖固定合成输入上的独立参考计算；不是G0放行、GitHub Actions CI、生产验收或用户本人独立验收。

## 1. 关闭依据与版本

评审依据为[G0覆盖矩阵M01](G0_fixture_coverage.md)的三维固定分组、同Scope、互斥穷尽、精确分数与来源追溯要求，以及[region方案RG01～RG06](../manual_checks/G0_M01_region_plan.md)、[测试矩阵](../manual_checks/G0_M01_region_test_matrix.md)和已审定M01-region-rules-v1。历史草案及旧评审状态保留原字节，本记录更新当前结论，不改冻结业务契约。

此前[局部评审](G0_M01_region_local_Must_review.md)指出的RG03.D多事件来源、RG05.A未知组来源已分别补齐；本轮不再修改测试或计算器，使用最终断言版本重新完成专项、相关及全量回归后才作关闭判断。既有category固定Oracle/测试及A3-11最小channel Must证据继续有效，并在相关回归中真实执行，不重开已完成的渠道最小Must。

| 关键文件 | 本轮SHA-256 |
| --- | --- |
| tests/test_reference_region_cohort.py | fd8dd9c2f754aad650a70a5a021fde6e17eeedd435d3bde3df34962c6df730ec |
| reference/region_cohort.py | 4652685bd2a104a047a09e62b8eb26c9aa400330fb1a2268bce4e00987c15dba |
| reference/manual_checks/G0_M01_region_expected.json | 50bca606d29077276d7a5d39c0c55dc0fbd57cfa5a0ff836db953bd9e301b1ce |
| 原11号Fixture | d652f050a45279f86b5900b76fdb1327ad9cefdaa114ad61a5d8e6457038f6f8 |
| M01-region-rules-v1文件 | 5322018b50b74da02b32c888b6777e9527fecd84b58d66b4a752ed664343c96c |

运行前核对Oracle及其全部sources哈希一致；原Fixture、独立台账、规则与预期未改。控制预期来自先行台账或其测试端静态迁移，只把固定字符串解码为Fraction，不由待测输出生成或写回expected。

## 2. 本轮真实执行

环境为CPython 3.10.12、pytest 9.1.1、Linux x86_64，复用既有.venv/bin/python，显式PYTHONPATH=src；未安装或修改依赖。实际安装FastAPI 0.141.1、Starlette 1.6.0、Pydantic 2.13.5、httpx 0.28.1、httpx2 2.13.0。既有API/TestClient在沙箱内停滞，本轮获准在沙箱外本地运行，不是CI。

| 顺序与范围 | 实际结果 | 退出码 |
| --- | --- | --- |
| 1. 开发树region专项，附-rA身份 | 39 passed in 0.25s | 0 |
| 2. 开发树region＋总体＋类别＋渠道＋静态Fixture | 149 passed in 0.50s | 0 |
| 4. 隔离公开候选全量pytest | 209 passed in 0.72s | 0 |

完整本地执行共四阶段；本公开版选列第1、2、4阶段，开发全量阶段留在本地。所选范围重叠，不累计数量。没有失败或跳过，没有为消除失败修改答案；209项为隔离公开候选本地全量，不是CI。

[公开执行输出选编](G0_M01_region_Must_closure_public_pytest.txt)保存公开候选59份指纹及三个所选阶段实际命令参数、全部39条region PASSED身份、stdout和退出码，SHA-256为`7a49e1c12820e66576e458448f7ecd4cf107e108142ab5678ed38e74b7ccf712`。这是2026-11-16真实执行的选编，不是2026-11-17重新运行；解释器机器路径以说明标签代称，其余argv保留。

[公开执行及断言清单](G0_M01_region_Must_closure_public_manifest.json)SHA-256为`39ccfb503d557253945e315c3f6488fc3150b3906cb4278a8a3311dfed890d7c`，绑定公开候选59份源码/测试/配置/Fixture/预期/规则文件、实际命令及39条PASSED身份。其内容与实际执行时一致、前后不变；函数选择器和assert行号索引保留，私有开发完整清单未纳入。

## 3. RG01～RG06直接断言与通过证据

下表数量只对region文件的39个实际pytest身份作不重叠归类；三维用例中各调用三个入口，不另算六个pytest。来源/守恒辅助函数和fixture保护由相关用例实际调用，不只是定义后未使用。

| 条目/通过项数 | 直接代码断言与独立预期 | 本轮判断 |
| --- | --- | --- |
| RG01 / 1 | matches_frozen_oracle_and_sources[RG01.W]完整对照四行及3/1→4/3、Fraction和变化；完整订单/退款键回查组来源，总体来源及东南排除集合逐项比较 | 单地区退化契约、先过滤再分组及来源通过 |
| RG02 / 2 | 同函数[RG02.A]对照两地区六行和来源，5/2→6/4、ΣN/ΣU守恒；absent_region_has_no_fabricated_zero_rate_row核对Q缺席组不输出、五行及精确变化 | 多地区有区分力分组及缺席组通过 |
| RG03 / 3 | D从实际去重订单回查两笔事件的refund_id/source_row_id配对、完整事件/订单键、success、当前支付窗及7天观察期，事件2但U=1；T跨日历窗仍归原支付窗，Z保留N=2/U=0/Fraction(0)，均完整比较先行预期 | 退款去重、归属、合法零退款及此前来源缺口通过 |
| RG04 / 15 | 两目录重复键2项、外域/快照4项，ValueError检查目录及完整键；过滤外产品缺失ready/immature2项；M/P/R不足及空基期4项，两窗指标和分组全部不发布；两个等号2项ready；过滤Scope成熟差异1项 | 复合键拒绝、关键关联优先级和比较门槛通过 |
| RG05 / 9 | explicit/unregistered两项完整七行、两窗成员及来源；手工原ID映射、支付/退款完整键及来源回查；同名不同ID1项，W排除未知2项，label=None保留ID1项，非法过滤/源地区null拒绝3项 | 稳定身份、未知保留/过滤隔离及此前来源缺口通过 |
| RG06 / 9 | 返回值污染/重复/交错调用及A联合逆序1项；W/A订单/退款/地区目录单独逆序6项，行/台账对照冻结Oracle且候选按集合；W/A三维共同Scope2项独立计算后分别对照冻结总计，各维分别守恒 | 输入隔离、重排不变性和三维共同Scope通过 |

RG01/02完整比较使用_assert_frozen；region_fixture核对固定Oracle及来源文件哈希、输入和Oracle内存前后相等、文件字节不变。_InputOnly禁止getitem/get/contains探测expected；三个入口各自从同一冻结input独立深拷贝计算，逐调用finally断言不变。

三维共同Scope测试不只比较三个输出彼此相等：每个维度先对照同一独立冻结N/U/Fraction、候选P和退款订单R；再核对行身份唯一、每窗唯一总计、每组成员唯一且退款从属支付、组集合互斥穷尽、ΣN/ΣU与总计一致。region仍完整对照自身四/六行，预期不来自category/channel输出，不把跨维行、率或贡献相加。

### 两个原阻塞缺口的本轮确认

- **RG03.D已齐备**：KR11-S-C-A1和KR11-RG03-S-C-SECOND的来源分别为r11-refund-s-c-app-1、r11-rg03-s-c-second；共同完整订单键为(domain_a,fixture_single_region_channel_v1_draft,K11-S-C-A1)，09-14支付、09-21成熟，两笔success发生于09-15/09-16，均在闭合H期且不晚于as_of。实际U及去重键集合大小均为1，不套用单事件来源假设。
- **RG05.A已齐备**：原Fixture地区SE到两个变体原始ID再到unknown的映射明确；unknown支付/退款集合均为{K11-S-C-A1}，来源和原退款完整键逐项对照冻结台账，当前SE仅剩K11-S-C-W1且无退款。基期、候选、总体、NW和两窗来源集合保持先行预期，未知1/1、SE剩余1/0。完整当前断言在本轮专项和两套全量中均通过。

## 4. 局部关闭决定及非阻塞剩余

RG01～RG06最小能力、三维共同Scope、先行独立Oracle、直接来源追溯、输入/冻结保护和当前版本完整回归均有直接断言及真实执行证据，满足本地M01最小参考层关闭条件。category/channel的既有固定回归亦无失败。因此关闭该局部Must，不再将已补齐的两个来源缺口保留为阻塞。

RG05.label-absent和RG06.W-reverse-combined仍未直接执行，保持此前评审的非阻塞补强定位：已有label=None代表缺展示名规则、W分别逆序及A联合逆序。其他坏格式/全组合未穷举，不冒称40个登记变体全部通过或所有完整控制输出均另冻为机器Oracle。C08继续为非阻塞Should，不因关闭评审升级为门槛。

这次关闭不会关闭M02合法跨域正例、M03贡献、M04其他关键退款DQ、M05真实独立签收、M06生产链路、M07正式评测或其他Should。G0整体仍未通过，生产授权、SQL、DQ状态映射、QueryEvidence、序列化及贡献能力不得由本地Fraction回归推定完成。

## 5. 公开与验收状态

公开候选从本地已提交公开b952916fd9ac78c15c0aae777759e9694d1628bc隔离复制，只加入当前两处来源断言及安全记录；原公开工作树和分支保持原状。旧提交的地区断言版本不是当前fd8dd9c2版本，不能将本轮209项追溯记到旧提交。最终公开交付仍须按候选59份映射核对实际提交内容。

开发全量及完整开发清单留在本地，不与公开候选结果混用；本公开版只提供安全的候选映射和所选执行阶段。原关闭评审当时未提交/推送，本次交付状态以最终提交和远程refs核验为准。

本结论是助手完成的代码/执行评审，不是用户本人独立验收或签字。没有触发/查询GitHub Actions CI，没有执行生产/正式评测；不把本地全量记为CI。原Fixture、冻结预期、规则、测试及参考/生产实现本轮均未修改，只有本次证据、评审及阶段状态发生追加。
