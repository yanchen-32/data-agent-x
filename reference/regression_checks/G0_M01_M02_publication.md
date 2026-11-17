# M01来源补强、局部关闭与M02草案公开交付

交付日期：2026-11-17（Asia/Shanghai）。父提交为b952916fd9ac78c15c0aae777759e9694d1628bc，沿独立公开历史正常快进。当前测试与2026-11-16最终执行版本一致；本次复用真实证据，不把交付日期写成新的pytest执行日期。

## 交付范围

本次白名单11文件：地区测试、RG03.D/RG05.A两份来源补强原始输出、地区阶段记录、局部Must评审、G0覆盖矩阵、最终关闭评审公开版、公开执行输出选编及候选版本清单、M02输入设计草案、本交付记录。

原RG03.D单用例和RG05.A两个参数用例内增加断言，没有新增pytest身份，地区收集仍为39项。RG03.D明确两笔成功事件的ID/来源配对、完整事件与共同订单键及闭合7天观察期，U只计1；RG05.A核对原始ID到unknown映射、完整七行、两窗成员及来源，未知1/1、当前东南剩余1/0，基期和总体不变。

原计算器、Fixture/expected、独立台账、规则与生产Runtime不变。开发Provider、内部归档、私有进度、环境同步记录及旧开发Git历史均不在公开范围。

## 真实执行及选编来源

实际执行日期2026-11-16，环境为CPython 3.10.12、pytest 9.1.1、Linux x86_64，复用既有虚拟环境，显式PYTHONPATH=src；没有安装依赖。

| 真实执行目录/范围 | 实际结果 | 退出码 |
| --- | --- | --- |
| 开发树region专项 | 39 passed in 0.25s | 0 |
| 开发树相关参考及静态Fixture | 149 passed in 0.50s | 0 |
| 隔离公开候选全量 | 209 passed in 0.72s | 0 |

所选范围重叠不相加。[公开输出](G0_M01_region_Must_closure_public_pytest.txt)明确标注为安全选编，逐段保留上述真实命令参数、stdout和退出码，删去私有开发完整文件清单及其全量阶段；完整本地原始证据原字节保留，原始输出SHA-256为171b177789de93e2cbe22caf938a07db474979a8a4767837ad09634ea6ae4f78。解释器机器路径沿用说明标签，其余argv保留，不假称新执行或完整本地输出的逐字副本。

[公开清单](G0_M01_region_Must_closure_public_manifest.json)仅包含候选59份运行/冻结文件映射、所选执行阶段、39条PASSED身份及RG01～RG06直接assert索引。提交前后将按该映射核对内容；测试源码自执行后没有再变化，因此无需重复测试来产生新数量。

| 对象 | SHA-256 |
| --- | --- |
| tests/test_reference_region_cohort.py | fd8dd9c2f754aad650a70a5a021fde6e17eeedd435d3bde3df34962c6df730ec |
| reference/region_cohort.py | 4652685bd2a104a047a09e62b8eb26c9aa400330fb1a2268bce4e00987c15dba |
| reference/manual_checks/G0_M01_region_expected.json | 50bca606d29077276d7a5d39c0c55dc0fbd57cfa5a0ff836db953bd9e301b1ce |
| G0_M01_region_Must_closure_public_pytest.txt | 7a49e1c12820e66576e458448f7ecd4cf107e108142ab5678ed38e74b7ccf712 |
| G0_M01_region_Must_closure_public_manifest.json | 39ccfb503d557253945e315c3f6488fc3150b3906cb4278a8a3311dfed890d7c |

RG03.D和RG05.A的单阶段原始输出分别保留a0e173b4054a31ff1d52aec5eba640ec5955f98a807a0b9e4f678828fa58ea33、2f8e60c5fee52551a681260c0a09aa3ccf5b1bf000cc6487d991d138642df704，不把最终复评结果追溯替换早期阶段输出。

## 关闭及后续状态

[最终关闭评审公开版](G0_M01_region_Must_closure.md)保持本地2026-11-16关闭结论：RG01～RG06最小参考层Must已具备直接断言和真实通过证据。公开版明确选编范围及与本地完整版的差别，不覆盖本地原文件，不将开发完整清单一起公开。旧公开文档全文保留，只追加当前状态。

[M02设计草案](../manual_checks/G0_M02_cross_domain_design.md)逐字交付：两个分别合法Scope复用局部ID和展示名，产品关联相反，A总率1/2→0，B总率1/2→2/3；先行逐单设计9笔支付和4笔退款。其静态自检不是参考计算或pytest，两个JSON输入和机器预期尚未创建/冻结，M02仍在准备阶段。

实际公开状态以最终提交和远程refs核验为准。本轮未手动触发或查询GitHub Actions CI，没有用户本人独立验收签字；M01参考层关闭不等于G0、生产授权/SQL/DQ、正式评测或其他Must通过。C08继续是非阻塞Should。
