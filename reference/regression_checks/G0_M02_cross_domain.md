# M02：合法跨域最小正例与交错调用回归

日期：2026-11-17（Asia/Shanghai）。结论：**M02-A/B均ready，固定结果和A→B→A、B→A→B交错调用与先行独立Oracle一致，最小正例计算回归在本地通过。** 原category回归无失败。本轮不作M02关闭评审，不等同生产隔离、CI、用户本人L3或G0通过。

## 1. 实施起点与冻结保护

实施前已有两份独立input和[已冻结Oracle v1](../manual_checks/G0_M02_cross_domain_expected.json)，没有M02专项pytest。本次新增[tests/test_reference_cross_domain_cohort.py](../../tests/test_reference_cross_domain_cohort.py)，只调用现有calculate_category_reference(input)，不改类别/总体计算器，不把两个Scope合并为一次查询。

测试先固定Oracle完整SHA-256为d6b831e08c943a259a56c4ed24db0dd153585c994c759685002dbc6be86ba8a6及rule_binding_version=M02-DD02-v1.2-design-v1，再逐项核对sources中设计/规则/Schema/两个输入的完整文件哈希、input规范化指纹及每case expected指纹。失败路径也由fixture的finally检查输入/Oracle内存和磁盘字节不变，不用当前文件重算新基线自证正确。

冻结依据及静态检查器首轮错误保留在[冻结记录](../manual_checks/G0_M02_cross_domain_freeze_review.md)，本轮不追改它们的“未执行pytest”历史状态或字节。以下执行记录推进后续计算状态，不修改已冻JSON。

## 2. 四个真实用例及直接断言

| pytest身份 | 实际调用及验证 |
| --- | --- |
| test_cross_domain_scope_matches_frozen_oracle_and_sources[M02-A] | A独立input，完整六行及2/1→2/0、精确率/变化、两窗P/R和来源逐项对照冻结A |
| 同函数[M02-B] | B独立input，完整六行及2/1→3/2、精确率/变化、两窗P/R和来源逐项对照冻结B |
| test_cross_domain_interleaving_keeps_each_frozen_scope[A-B-A] | 同一进程、各自独立input对象，逐次直接对照各case冻结预期；旧返回值及两输入均保持不变 |
| 同函数[B-A-B] | 反向交错重复验证，不以第一次实际输出生成后续expected或参考基线 |

每轮专项收集4个pytest身份；交错每个身份含三次入口调用，不能把调用次数当作新增pytest数量。_InputOnly及输入前后deepcopy保护复用现有机制；expected只在断言端解码Fraction，不传给计算器。原category的assert_partition辅助断言复用，不重写另一套分组Oracle；原category/channel测试文件不修改。

各次返回均先检查outcome=ready及完整字段集合，随后完整对照冻结六行、metrics、quality、分组支付/退款台账；候选按集合和唯一性比较。计数必须为int，所有率及两项变化必须为Fraction，不用浮点容差。

| Scope | 基期N/U/率 | 当前N/U/率 | 绝对变化 | 相对变化 |
| --- | --- | --- | --- | --- |
| A | 2/1，1/2 | 2/0，0 | −1/2 | −1 |
| B | 2/1，1/2 | 3/2，2/3 | 1/6 | 1/3 |

## 3. 完整事实键、产品关联和来源

测试从**实际返回的候选及分组成员**恢复(domain_id,snapshot_id,order_id)，与冻结evidence中的完整P/R键集合直接比较；不能只比A/B碰巧相同的基期总率。组支付/退款分别互斥穷尽，退款属于本组支付，ΣN/ΣU等于本Scope总计。

逐实际支付成员按完整键回查原始订单和source_order_ledger，核对source_row_id、支付时间、支付窗及类别归属，再用完整产品键与类别键核对反转映射、目录来源及展示名。A的product_1→category_1，B的product_1→category_2；B基期category_1成员为order_b_2，不接受沿用A的order_b_1。

从实际去重退款订单完整键集合回查原始事件，与先行列明的完整refund_key及事件来源逐项比较；核对order_key、source_row_id、success、refund_at、所属支付窗及类别。每组和每窗支付来源/事件/退款来源分别匹配冻结集合，原始四类目录也按完整键及来源核对。固定输入事件的资格已由先行台账冻结，本轮测试不重新扫描时间条件来生成退款Oracle。

交错用例另证明测试前提确有局部ID碰撞：A/B共享四个order_id及refund_shared_1，但完整订单/事件键集合不相交。A/B的refund_shared_1各回查自己的来源并关联不同订单；每次完整结果及来源均对照自己Scope的冻结值。后续调用后检查此前所有返回值仍等于保存的深拷贝，防止共用结果对象或跨调用状态污染。

参考输出行未新增域字段，测试始终与对应input完整context绑定，不按局部聚合行ID跨域合并，不以source_row_id前缀推断真实授权。此配对故意保持同一局部snapshot_id，主要验证不同域的合法调用不串数，不冒称同域不同快照正例或数据库/角色隔离已验收。

## 4. 本轮真实执行

环境：本地开发工作树、.venv/bin/python、CPython 3.10.12、pytest 9.1.1、Linux x86_64，显式PYTHONPATH=src；没有安装依赖。实际按以下顺序执行，全部退出0，没有失败或跳过：

| 实际范围 | 实际结果 | 退出码 |
| --- | --- | --- |
| M02专项，附-rA身份 | 4 passed in 0.25s | 0 |
| 原tests/test_reference_category_cohort.py | 38 passed in 0.12s | 0 |
| M02＋类别＋地区＋渠道＋总体＋静态Fixture | 153 passed in 0.75s | 0 |

三次范围重叠，不累计测试数量；153项是实际输出，不从旧数量推算通过。原category38项被单独实际运行，相关地区/渠道/总体和静态Fixture也在组合内真实通过。未修改冻结预期迎合实现，没有运行全量、公开候选或CI。

完整命令、stdout、退出码、四个测试身份和运行版本见[G0_M02_cross_domain_pytest.txt](G0_M02_cross_domain_pytest.txt)，SHA-256为eead6e80b7a048b3e70bab434461c3e5f8adeabb3cf87b793558645a85ca0e89。

| 运行绑定文件 | SHA-256 |
| --- | --- |
| tests/test_reference_cross_domain_cohort.py | d0d0b6ac618e11f7bc1fe524b0754b8309ede979d5eb81cbd22476250299d1ad |
| 原category测试 | f5be1f6e7740ed43f26231eaa62d51f75b59d4e16baf2e26821b71becd0387a5 |
| reference/category_cohort.py | 53507d6ba6671e7ca7ca6cd4f955fa345b53be73bf98edf5fd638d5206f2b216 |
| reference/cohort.py | 13b5ced6824c1b8548eaa55b8014f4f87c35562fbe24eead2f0408afbefa96c6 |
| 冻结Oracle | d6b831e08c943a259a56c4ed24db0dd153585c994c759685002dbc6be86ba8a6 |
| A完整输入JSON | 66e23c0f5988eefb3ef84b7ec0533fb601d4645e2dbbe494a30d79118b58f31a |
| B完整输入JSON | 77ebe993f50b56dbe22dfc0c50cd64d61e479b116afb9fe871becddece88b24e |

完整来源及规则的版本由固定Oracle.sources进一步绑定，全部在每个用例前后检查。当前开发HEAD不能替代这些尚未提交文件的运行版本。

## 5. 本轮边界和后续状态

本轮只新增专项测试、原始输出及本文，并追加阶段状态；冻结Oracle、输入、设计/规则、参考/生产代码、所有原测试、历史输出和Provider保持原字节。未提交/推送，不称公开交付、GitHub Actions CI或用户本人独立验收。

M02最小合法配对及交错调用本地计算通过，后续整体回归、公开候选版本绑定或局部关闭评审应按实际执行另行登记；本轮不自动关闭M02/G0，也不新增生产授权、SQL或真实跨域访问能力。M01已关闭的本地参考范围保持。
