# M02：合法跨域配对输入装配与指纹记录

日期：2026-11-17（Asia/Shanghai）。状态：**两份独立合成输入草稿已创建，并通过标准库静态装配检查；未冻结、未调用参考函数、未作pytest计算回归。** M02尚未验收，不增加已冻结主Fixture数量。

## 1. 设计依据与独立文件

本轮严格转录[既有设计稿](G0_M02_cross_domain_design.md)，其SHA-256为9a80e46c09cdd81ac316f18b6d5effa7dd2596e31a157b90740a4934d77b5159，原文不改。本次新增文件均放在既有fixture_drafts目录：

| 文件 | 完整Scope | 订单/退款 | 窗口内支付数量（输入诊断） |
| --- | --- | --- | --- |
| [m02_cross_domain_scope_a.json](../fixture_drafts/m02_cross_domain_scope_a.json) | (domain_m02_a,snapshot_m02_pair_v1) | 4/1 | 基期2、当前2 |
| [m02_cross_domain_scope_b.json](../fixture_drafts/m02_cross_domain_scope_b.json) | (domain_m02_b,snapshot_m02_pair_v1) | 5/3 | 基期2、当前3 |

每份文件独立包含元数据及input；input仅含context/orders/refunds/dimensions，没有expected或权限开关。planned_dimension=category、授权合成前提及草稿状态都在input外。不是一次合并查询，也不是已批准生产快照。

两个Scope复用局部snapshot_id、四个order_id、refund_shared_1、产品及维度ID/展示名；域字段不同。A中product_1/2分别关联category_1/2，B映射反转；同名退款事件在A/B分别关联order_b_1、order_b_2。B额外保留order_c_3及两笔当前退款，A当前不含退款。以上只登记输入事实，不在本轮生成指标输出或机器Oracle。

## 2. 输入与完整文件SHA-256

| 对象 | SHA-256 |
| --- | --- |
| A规范化input | 2f0da4cb15e390f5042e32443415aa4e1d40ed1b510638e833fe13027eddbdcf |
| A完整JSON文件 | 66e23c0f5988eefb3ef84b7ec0533fb601d4645e2dbbe494a30d79118b58f31a |
| B规范化input | 8ef18ba042f9f6282391a3ff45575c043cf37a4f5365e744e00502bfb08169ce |
| B完整JSON文件 | 77ebe993f50b56dbe22dfc0c50cd64d61e479b116afb9fe871becddece88b24e |

规范化规则：UTF-8编码json.dumps(input,ensure_ascii=False,sort_keys=True,separators=(',',':'))，不含尾换行；数组顺序参与指纹。完整文件哈希覆盖实际字节及尾换行。各JSON元数据input_sha256保存前一种指纹，完整文件指纹在此单独保存，避免文件包含自身哈希的循环。两种指纹不可混用。

这些是本轮输入版本绑定，不是业务expected冻结或approved dataset_manifest；后续若调整草稿须记录差异并重新核对，不覆盖既有正式Fixture或假称旧哈希仍适用。

## 3. 本轮实际静态检查

装配按人工逐单设计录入，只以标准库做JSON机械序列化；验证脚本另从原Markdown第2～5节解析共同context、支付、退款及产品表，对落盘JSON逐字段比较，没有使用装配脚本中的输入列表充当验证答案。

实际命令为python3 -（标准库检查脚本经stdin执行），环境CPython 3.10.12；完整stdout见[G0_M02_input_check.txt](../regression_checks/G0_M02_input_check.txt)，SHA-256为6b02aafc98f58fc7c73ee35bf79724896225985f455c943d5e34b275cfb11f6a。实际退出码0，检查如下：

- 每行domain_id/snapshot_id与自身context一致；订单、退款事件及四类目录的完整键分别唯一，没有跨域行或裸ID覆盖。两个输入之间完整订单/事件键不相交，局部ID按设计复用。
- 产品2/类别2/地区1/渠道1在每个Scope内完整登记；产品→类别反转与手工表一致，所有订单产品、地区、渠道关联成功，单地区过滤ID已登记。
- 9笔有效支付处于各自半开支付窗，字段和来源与逐单表一致；H=604800秒。A最晚09-17、B最晚09-18成熟，均≤as_of及退款水位09-23；支付水位09-15覆盖窗口末端，两窗均非空。
- 4笔事件均success且完整订单键关联存在；退款时间在各自[paid_at,paid_at+7天]且≤as_of，不含孤立、支付前或重复事件。source_row_id与设计稿逐笔对应，连同12条目录来源共25条，全部唯一。
- 元数据设计哈希及input_sha256与实际字节一致；读取前后两份JSON及原设计稿不变。没有生成或写回答案，没有调用reference/dataagentx或pytest。

静态检查中的订单数量、时间和关联仅是输入诊断，不冒称calculate_category_reference已经返回结果，也不把两个文件读入同一检查脚本等同于合并成一个查询input。

## 4. 当前实施边界

本轮只创建两份输入、此记录和静态输出，并追加阶段状态。旧设计、已冻结Fixture/expected、源码、测试、M01证据及原有Provider工作不变，未新增框架或计算器，未提交/推送。

独立机器expected、两份输入的正式冻结记录和固定/交错调用pytest仍待后续分别完成；应沿既有逐单台账保存先行预期再运行，不从参考函数反推答案。M01本地参考层关闭保持，M02输入可进入下一阶段，但M02计算回归、CI、用户本人L3、G0及生产授权均未通过本轮静态检查自动验收。

## 公开选编说明（2026-11-17）

本文公开版仅移除指向本地分支/工作树检查记录的链接及其阶段说明，输入指纹、装配规则、静态结果与后续待办保留原阶段含义。原本地记录不覆盖；当前冻结和计算状态见[M02回归](../regression_checks/G0_M02_cross_domain.md)，交付状态见[公开交付记录](../regression_checks/G0_M02_publication.md)。
