# M01：RG05/RG06增量及局部评审公开交付

日期：2026-11-13（Asia/Shanghai）。本轮公开候选基于独立公开父提交7530cb9cbde5c638ade41b918992992ff2849a7d，追加RG05/RG06测试及真实回归/评审证据。**回归通过，M01参考层仍开放；不声明G0或生产验收通过。**

## 交付范围

本次地区测试由28项增至39项，新增11项：同名地区身份1项、单地区过滤排除两种未知来源2项、W/A三维共同Scope2项，以及W/A分别逆序订单/退款/地区目录6项。原重复调用、返回值隔离、A联合逆序和其他测试保留。

新增控制均复用原冻结变体和指纹，region数值真值仍由既有独立Oracle提供；不把category/channel输出当作region预期。各维分别核对Scope与N/U守恒，不跨维相加。原Fixture、expected、规则、参考计算器、生产Runtime和依赖配置均不修改。

本次白名单为10个文件：地区测试、地区回归记录、G0覆盖矩阵、三份RG05/RG06阶段原始输出、局部关闭评审、该评审的原始输出及版本清单，以及本文件。公开文档保留此前全文并追加状态，不以开发文档整体覆盖公开版本；开发Provider、私有进度、环境同步记录和旧开发Git历史不在范围内。

## 实际执行及提交版本绑定

隔离候选由已提交公开父树复制，测试代码与本轮公开工作树逐字节一致。环境为CPython 3.10.12、pytest 9.1.1、Linux x86_64，复用既有虚拟环境并显式PYTHONPATH=src；未安装依赖。

| 实际运行目录与范围 | 实际结果 | 退出码 |
| --- | --- | --- |
| 开发树region专项 | 39 passed in 0.23s | 0 |
| 开发树region＋总体＋类别＋渠道＋静态Fixture | 149 passed in 0.46s | 0 |
| 隔离公开候选全量pytest | 209 passed in 0.76s | 0 |

范围重叠不累计。无失败或按实际结果改写预期。原始输出中仅将解释器机器路径替换为说明标签，其余实际命令参数、stdout及退出码保留；复现时以具备相同依赖的Python替换该标签。

[执行清单](G0_M01_region_local_review_manifest.json)分别绑定开发及公开候选各59份运行/冻结来源文件。本次公开源码按public_candidate映射核对；development映射只对应开发阶段，不与公开配置混用。测试与计算器/输入在测试完成后均未变化，因此本次复用该真实执行证据，不将另一次未执行的测试写成新结果。提交前及提交后仍须核对59份文件与清单一致。

| 关键文件 | SHA-256 |
| --- | --- |
| tests/test_reference_region_cohort.py | 09a611917d87e492b8e58ea01ade88c045d3a314cd2e191ca8231297fbfafb71 |
| reference/region_cohort.py | 4652685bd2a104a047a09e62b8eb26c9aa400330fb1a2268bce4e00987c15dba |
| reference/manual_checks/G0_M01_region_expected.json | 50bca606d29077276d7a5d39c0c55dc0fbd57cfa5a0ff836db953bd9e301b1ce |
| [局部评审原始输出](G0_M01_region_local_review_pytest.txt) | 3028a08978c098cf18e984644b48efd3608b46f6357a22d41a926663d454dbd2 |
| G0_M01_region_local_review_manifest.json | e849f81dfb722bac79cd9257a0dd998ccc2fb08da44fda067ebc1f6e9ac81578 |

[RG05原始输出](G0_M01_region_RG05_pytest.txt)、[三维共同Scope输出](G0_M01_region_RG06_common_scope_pytest.txt)、[独立重排输出](G0_M01_region_RG06_reorder_pytest.txt)保持各阶段原字节和测试版本，不用最终39项版本追溯改写其31/33项等历史结果。

## 关闭结论和公开边界

[RG01～RG06逐项评审](G0_M01_region_local_Must_review.md)保留两处局部Must来源证据缺口：RG03.D需要直接核对同单多笔有效事件及其来源，RG05全地区未知控制需要完整核对原ID归类、支付/退款来源及未受影响的成员。数值计算通过不等于来源断言完整，M01参考层因此仍开放。缺label字段和W联合逆序保留未执行补强状态；C08继续是非阻塞Should。

上轮评审中的“未提交/推送”描述保留其当时状态，本次交付以最终提交和远程refs核验为准。209项是隔离公开候选本地全量结果，不是旧父提交、GitHub Actions CI、生产授权/DQ或用户本人L3验收。未触发或查询CI，不代签本人验收，不关闭G0或其他Must。
