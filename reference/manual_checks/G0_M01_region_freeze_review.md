# G0 M01：region独立Oracle v1冻结记录

日期：2026-11-10（Asia/Shanghai）。结论：**RG01.W四行及RG02.A六行的开发数值/来源Oracle v1已冻结**，产物为[G0_M01_region_expected.json](G0_M01_region_expected.json)。另登记40个已列明输入变体的变更及指纹，完整业务预期冻结范围仅限RG01/RG02；不是region实现、pytest、生产授权、CI或用户本人独立验收通过。

## 1. 独立来源与转录方法

数值唯一来源为[2fe6d51](https://github.com/yanchen-32/data-agent-x/commit/2fe6d51d9c1f0797b09930b875a47e4f70f2ada6)已提交的[114行人工台账](G0_M01_region_expected_draft.md)，本轮验证其本地字节与提交树完全相同，SHA-256为99040571560c27f8eadd84ce72ee4640a53f25a6eadfaff8ffd6ba4705fc9fe3。作者已知历史总计，不称首次盲审或用户本人签字。

§2的11笔支付及成熟日、§3的六笔合格退款和来源、§4的四组P/R集合和全地区六行直接结构化；W四行及两Scope总体变化从§4文字手填。集合按ID排序只作序列化规范，来源关联只连接人工表已明确的订单/事件，不从原始input重新判定分组或计算N/U，也不合并channel输出产生region真值。

没有导入或调用待测region、总体/类别/渠道参考函数、生产代码或SQL。仅使用标准库转录人工表、装配明确输入变更、计算SHA-256，并在JSON保存后静态复核来源和Fraction算术；检查不写回答案。

## 2. 规则和原文件绑定

| 对象 | 绑定 |
| --- | --- |
| 规则版本 | M01-region-rules-v1 |
| [规则审定文件](G0_M01_region_rule_review.md) | SHA-256 5322018b50b74da02b32c888b6777e9527fecd84b58d66b4a752ed664343c96c |
| [原11号Fixture](../../tests/fixtures/order_boundaries/11_single_region_channel_grouping.json)完整文件 | SHA-256 d652f050a45279f86b5900b76fdb1327ad9cefdaa114ad61a5d8e6457038f6f8 |
| 原Fixture规范化input | SHA-256 459879d55d0ebbd0ed4103a628d1946d5e9c58f2aff7e8bbdbcf9804a4f85257 |
| 原A3-11独立expected完整文件 | SHA-256 c0e82fc22fb028235f249d524e516920b733636f7ad22ecbb53d7a7b6e811a7e；只作保护绑定，不作为新地区分组答案生成器 |
| [方案原稿](G0_M01_region_plan.md) | SHA-256 20200d0af6c99bf4118d7ea0d81ebd22ab1f3a03084148b79606da56d1949b2c |
| [矩阵原稿](G0_M01_region_test_matrix.md) | SHA-256 8da7fd865cb1bd590d6c4b457490ccf4638e9a32e23d61f637d8e8aa23e2b7e1 |
| 本次冻结JSON完整文件 | **SHA-256 50bca606d29077276d7a5d39c0c55dc0fbd57cfa5a0ff836db953bd9e301b1ce** |

JSON的sources还逐一绑定DD02、SRS、指标目录及对象Schema原文件指纹。规则审定文件在冻结时为本地新增记录，未包含于2fe6d51，不能声称该公开提交已有本次规则/JSON；其确切版本由文件哈希绑定。规则、旧草案和已提交人工台账均保留原字节及历史状态，本记录推进后续冻结，不追溯改写它们。

所有规范化指纹均为UTF-8编码的`json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))`，不含末尾换行。输入数组不重排后再算哈希，因此重排变体即使集合相同也独立绑定。完整文件SHA-256则覆盖实际磁盘字节，包含文件末尾换行。

## 3. RG01/RG02冻结内容

| 冻结案例 | 输入变更/指纹 | 业务预期 |
| --- | --- | --- |
| RG01.W | 原input不改，filters.region_ids=["region_northwest"]；input SHA-256=459879d55d0ebbd0ed4103a628d1946d5e9c58f2aff7e8bbdbcf9804a4f85257 | 四行：基期总计及NW均N=3/U=1/率1/3，当前总计及NW均4/3/率3/4；绝对变化5/12，相对5/4；max(paid_at+H)=09-19 |
| RG02.A | 仅在深拷贝中将过滤列表改为[]；input SHA-256=46b72e78ff75d2bbad685d1923efea250e1cd624af92d09d9f6004466d26d169 | 六行：基期NW=3/1、SE=2/1，总计5/2/率2/5；当前NW=4/3、SE=2/1，总计6/4/率2/3；绝对变化4/15，相对2/3；max(paid_at+H)=09-21 |

两案例均ready、reasons=[]，总体原有三个成熟/水位quality标志均true；原支付水位09-15等于最大窗口end。率及变化为精确有理数字符串，读取端用Fraction解析，不能转float/误差近似；计数为整数，这不是生产Decimal序列化器。

JSON中`cases[case_id].expected`保存聚合行、metrics、候选及分组支付/退款订单集合等应比较字段；`evidence`保存独立的支付来源、事件/退款来源、目录来源、排除集合和成熟上界，只供测试端回查，不要求参考函数返回这些元数据。`source_order_ledger`覆盖11笔原始支付的完整业务键、原地区、支付/成熟时刻、产品键及来源；`source_refund_ledger`覆盖六笔原始退款的完整事件/订单键、时刻、来源和人工归属。

每个预期包另有规范化SHA-256：

- RG01.W expected：4bf1651b89c9e02ac35f618f628e0d5485353cf8ebc98e79db595db23e7d5d09。
- RG02.A expected：7c07e96251d4699befa0f24fb85dee112ae5300b10552420531aff1477e8d2cd。

聚合行身份先检查(window_index,dimension_id,group_id)唯一，再比较；各组支付/退款成员、候选和来源按集合核对且检查唯一性。W的四笔SE支付及两笔SE退款来源全部排除，A的两地区各组互斥穷尽；不能仅以总计/行数相等判通过。

## 4. 合成变体指纹范围与授权边界

`input_variants`包含40项，包括W/A、台账明确的D/T/Z、成熟/水位/空窗/缺席组、展示名/未知/非法参数，以及矩阵明确的目录/关键产品/Scope对照和W/A重排。每项含父变体ID、精确变更、指纹及来源章节；只有RG01.W和RG02.A指向本次冻结的完整expected，其他项明确标“仅绑定输入指纹”。它们的后续完整业务Oracle仍须按已有人工规则单独冻结，不能因登记了哈希就标业务结果通过。

变体映射整体规范化SHA-256为fd4a4d3a1e191f4f767602213e6e92f38941b9224f87baa4d358f6ca1b5fd271。重复调用和三维调用本身不改变输入字节，引用原W/A；单独逆序订单/退款/地区目录及三者联合逆序在W/A下各有独立指纹。没有新增主Fixture或修改原输入。

A及其控制均明确“合成主体假定获准访问整个固定两地区输入”，不是原W任务的过滤覆写或生产授权证据。未知相关控制仍以已纳入受控输入、非关键缺失为前提；授权不明时不得靠unknown放行。本文件授权说明仅为冻结案例元数据，不新增生产输入开关、权限实现或HTTP状态。

## 5. 本轮实际静态核对

环境为Python 3.10.12，使用标准库。转录由一次性结构化脚本完成；实际静态核对以`python3 -`经标准输入执行，不使用pytest或业务函数。静态核对在JSON写入后运行，验证前后JSON字节相同。实际核对输出、退出码0：

```text
RG01.W：4条聚合行、Fraction、订单/退款集合与来源守恒静态核对通过。
RG02.A：6条聚合行、Fraction、订单/退款集合与来源守恒静态核对通过。
40个已列明输入变体指纹重放一致；原114行台账及规则/Fixture来源指纹一致。
静态核对退出码0；未调用参考/生产函数、未运行pytest、未写回任何预期。
冻结JSON SHA-256：50bca606d29077276d7a5d39c0c55dc0fbd57cfa5a0ff836db953bd9e301b1ce
```

具体检查包括：原114行台账与提交树相同；所有sources哈希一致；逐笔支付/退款键、字段和来源匹配原input；人工成熟日、支付窗、退款观察期合法；两案例原列表身份唯一、Fraction算术、组成员互斥穷尽、ΣN/ΣU与独立总计一致；来源及排除集合一致；40个变体仅重放显式变更后重算指纹，不计算业务预期。该静态审计不等于参考实现已通过。

## 6. 后续使用与阶段状态

后续先固定本JSON及规则/来源哈希，再从原input装配所选变体并检查input指纹，然后只把input传入拟实现的calculate_region_reference；测试从本JSON读取expected和证据。发现差异先定位实现/Scope/规则，不改冻结v1迎合输出；确需修订须另存版本及差异理由，保留旧证据。

本轮只新增机器可读Oracle和本记录，并给G0矩阵追加阶段入口；旧Fixture/expected、114行人工台账、规则审定、DD02/SRS/Schema、已有源码/测试及原执行输出保持不变。未创建region计算器/pytest测试、未运行pytest、未修改生产Runtime/授权、未提交推送；M01/G0仍开放，A3-11渠道Must和C08非阻塞Should边界不变。冻结只表示先行开发Oracle已经固定，不代表本人独立验收或生产批准。
