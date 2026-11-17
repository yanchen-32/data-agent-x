# M02：合法跨域配对独立Oracle v1冻结记录

日期：2026-11-17（Asia/Shanghai）。结论：**M02-A/B开发数值、成员及来源Oracle v1已冻结**，产物为[G0_M02_cross_domain_expected.json](G0_M02_cross_domain_expected.json)。A总率1/2→0，B总率1/2→2/3；各域分别满足分组互斥穷尽和ΣN/ΣU守恒。本轮未运行参考函数或pytest，不表示M02计算回归、CI、生产批准或用户本人验收通过。

## 1. 独立先行来源及转录方法

数值与P/R唯一先行来源为已提交[设计及逐单台账](G0_M02_cross_domain_design.md)§4～6，公开提交[bccd60e](https://github.com/yanchen-32/data-agent-x/commit/bccd60ef3ee278a4022cd780d450dfb531c13519)。本轮只读取本地该提交对象，确认台账字节与工作树相同；SHA-256为9a80e46c09cdd81ac316f18b6d5effa7dd2596e31a157b90740a4934d77b5159。

成员、逐组N/U、率、变化、逐单支付/成熟日期及退款来源直接手工转录，再以标准库机械结构化、装饰完整键和记录指纹。目录身份/来源和context仅从已绑定输入机械复制；不扫描输入生成新的分组答案，不调用calculate_reference、calculate_category_reference或其他参考/生产函数、SQL或运行输出生成expected。

结构化JSON保存后，另从原Markdown表格解析独立成员/数值，回查两份原始输入并用Fraction核对算术；检查只比较，不回填预期。作者已知先行预期，不称首次盲审、用户签字或另一名独立审核者验收。

## 2. 规则、设计与两份输入绑定

Oracle的rule_binding_version为M02-DD02-v1.2-design-v1，仅命名既有DD02 v1.2、指标目录及指定设计稿哈希的组合，不新增业务规则或生产metric_version。baseline沿用DAX-RB-1.2.1，metric_version仍为null；不会虚构已批准manifest或已安装的指标版本。

| 绑定对象 | SHA-256 |
| --- | --- |
| DD02 v1.2 | 3c5452e0121db488da05686bdbda8d8ec38dc4107ed71837862943e518fc83b0 |
| 指标目录 v1.2 | 51b2d179259c7e6d077491d319bf5da7b0f477c817d55db90dcb10861c0a2bce |
| 对象Schema v1.2.1 | e50b08ca770ef699dcc58db246782ff800eb2e7c856c9558369c25022528383a |
| 设计/逐单台账版本 | 9a80e46c09cdd81ac316f18b6d5effa7dd2596e31a157b90740a4934d77b5159 |
| [A输入完整文件](../fixture_drafts/m02_cross_domain_scope_a.json) | 66e23c0f5988eefb3ef84b7ec0533fb601d4645e2dbbe494a30d79118b58f31a |
| A规范化input | 2f0da4cb15e390f5042e32443415aa4e1d40ed1b510638e833fe13027eddbdcf |
| [B输入完整文件](../fixture_drafts/m02_cross_domain_scope_b.json) | 77ebe993f50b56dbe22dfc0c50cd64d61e479b116afb9fe871becddece88b24e |
| B规范化input | 8ef18ba042f9f6282391a3ff45575c043cf37a4f5365e744e00502bfb08169ce |
| **本次Oracle完整文件** | **d6b831e08c943a259a56c4ed24db0dd153585c994c759685002dbc6be86ba8a6** |

规范化规则为UTF-8编码json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))，不含尾换行；输入数组不重排。完整文件SHA-256覆盖实际字节及尾换行，不与规范化input或expected指纹混用。

输入仍在fixture_drafts路径，元数据及字节均不改。本次冻结的是绑定当前输入版本的独立开发Oracle，不移动主Fixture、不追改输入中早期草稿状态，也不冒称两输入已提交或生产批准。后续输入或规则若需变化，应另行版本和差异审定，不能静默更新本次基线哈希。

## 3. 冻结预期与来源结构

cases.M02-A/B分别保留完整context、六条aggregate_rows、metrics、candidate_order_ids、group_order_ids和group_refunded_order_ids。A与B分别调用，不把任何一方输出当作另一方预期。

| Scope/窗口 | category_1：N/U/率 | category_2：N/U/率 | 总计：N/U/率 |
| --- | --- | --- | --- |
| A基期 | 1/1，1 | 1/0，0 | 2/1，1/2 |
| A当前 | 1/0，0 | 1/0，0 | 2/0，0 |
| B基期 | 1/1，1 | 1/0，0 | 2/1，1/2 |
| B当前 | 2/1，1/2 | 1/1，1 | 3/2，2/3 |

A绝对变化−1/2、相对变化−1；B绝对变化1/6、相对变化1/3。所有计数是整数，率及变化是精确有理数字符串，后续断言用Fraction解码；不是生产Decimal序列化。两者ready、reasons=[]，三个quality标志均true。

独立成员及退款集合保留台账字面值：

- A基期category_1支付/退款均{order_b_1}，category_2支付{order_b_2}、退款空；当前category_1/2分别支付{order_c_1}/{order_c_2}，两组退款均空。
- B基期category_1支付/退款均{order_b_2}，category_2支付{order_b_1}、退款空；当前category_1支付{order_c_2,order_c_3}、退款{order_c_3}，category_2支付/退款均{order_c_1}。
- A基期退款事件refund_shared_1来源m02-a-refund-1，B同名事件来源m02-b-refund-1且关联另一笔基期订单；B当前事件refund_shared_2/3分别来源m02-b-refund-2/3，归category_2/1。不能按裸refund_id跨域去重或复用关联。

每case的source_order_ledger/source_refund_ledger保存9笔支付、4笔事件在各自域/快照内的完整键、时间、来源和人工归属；catalog_ledger另保存12条目录来源、完整键、展示名及产品类别映射。evidence逐窗/组保存支付来源、退款事件ID和退款来源，另存完整候选/退款订单键；它们只供测试端回查，不要求参考函数新增来源字段。

两case按各自context隔离相同局部ID，25条source_row_id唯一。pair_contract明确四个共享局部order_id和refund_shared_1，完整订单/事件键不相交；这不是一份跨域合并查询或生产授权开关。

每个expected对象另绑定规范化指纹：A为dbd2eb3a1d42533d9d0ce6a247d1455c51449cd2ea0760103b93336be7e7be1f，B为76b45bd9b2a7be877772b483ad5612b769f5842d972c71e3e01e120af7461e81；整个JSON哈希还保护evidence、逐单来源和规则绑定，不能只验证expected子对象忽略其余内容。

## 4. 实际静态检查与首轮失败保留

环境为CPython 3.10.12，命令python3 -（标准库脚本经stdin执行）；没有安装依赖、运行参考函数或pytest。

首轮检查器在目录对照处错误地将categories的主键category_id与products才保存的外键字段作同样比较，返回AssertionError、退出码1。结构化目录已在key中保存类别主键，Oracle内容与原台账无差异；只修正检查器按目录分别核对产品外键或展示名，**没有修改Oracle或输入**。失败stdout及工具返回的stderr保留于[G0_M02_oracle_freeze_check_attempt_01.txt](../regression_checks/G0_M02_oracle_freeze_check_attempt_01.txt)，SHA-256为1a2d3160baf0f93cbce26bd877ab123f845c8374e07f197965fc44250d128e13。

重验实际退出码0，完整输出见[G0_M02_oracle_freeze_check.txt](../regression_checks/G0_M02_oracle_freeze_check.txt)，SHA-256为7d171437296b29fcb2925607c2ff120eb55e71f1e88e84e5330a43398faf3629。检查包含：

1. 全部来源文件、两个完整输入及规范化input指纹与绑定一致；context匹配，所有事实/目录完整键唯一、Scope与关联合法。
2. 九笔支付和四笔退款逐项匹配已提交Markdown及原始输入；支付窗、7天成熟、水位、success和闭合观察期合法，人工归属及产品类别映射一致。
3. 每域六行身份唯一；四个类别P/R与台账逐项一致、互斥穷尽，N/U与成员数相符，ΣN/ΣU分别等于本域总计，精确率及变化的Fraction静态算术一致。
4. 每窗/组的支付来源、退款事件和来源集合与逐单台账相符；25条来源唯一，局部ID跨域复用但完整事实键不相交。
5. 两次检查之间及重验前后Oracle完整文件SHA-256均为d6b831e08c943a259a56c4ed24db0dd153585c994c759685002dbc6be86ba8a6，原输入/设计/规则字节不变。

这是独立Oracle冻结的静态一致性证据，不是M02计算器实际输出或pytest通过。首轮审计失败没有删去，也没有用调整预期掩盖。

## 5. 后续使用边界

后续测试须先固定本JSON及来源哈希，只把每个case所绑定的input分别传给现有类别入口；实际结果再与先行expected逐项比较，回查evidence及完整键来源，并核对交错调用不串数。参考源码版本和真实pytest结果应另行绑定，不能用本轮静态检查替代。

本轮未修改输入、设计、规则、源码、测试、旧Fixture/Oracle或既有开发工作；仅新增冻结Oracle、此记录及两份静态检查证据，并追加阶段状态。未提交/推送，未取得CI或本人独立验收；M01本地关闭保持，M02计算回归、G0、正式评测与生产授权仍未通过。
