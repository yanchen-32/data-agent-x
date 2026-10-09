# DD04 检索证据与报告 v1.2

日期：2026-10-09；基线DAX-RB-1.2。状态：设计规格已修订，应用实现/运行验收待完成。控制依据：[SRS v1.2](../01_需求基线/DataAgentX_SRS_v1.2.md)。本版完整替代同模块v1.0/v1.1实施指导，旧版保留历史。

<a id="retrieval"></a>
## 1. 精确目录与最小检索

指标/Schema/权限/水位精确读取版本化目录，不靠全文检索决定公式。审核业务规则文件用BM25：中文2gram、英文规范词；800字符chunk/100重叠、top5、稳定ID破同分。domain/approved/version/有效区间筛选在IDF统计和排名之前，禁止先全库排名再过滤造成信息泄漏。知识版本manifest不可变，cache绑定域/权限版本/知识hash/查询配置。

CAL-R01先≥20开发查询，审阅canonical相关全集R/必要集C/0–2相关级；正式≥60独立查询。Recall@5同时报min(5,|R|)/|R|上限，Hit/MRR/nDCG（gain=2^rel−1）、关键证据和端到端证据召回；R=0排名N/A，正确拒绝另报。数值门槛尚未冻结，必须预实验后记录理由/标签与配置hash、正式前冻结；不能无条件写Recall≥0.80或盲测后调低。词法不足先分析切分/标签，单一Dense可作为F08替代候选，完整四策略F19为Should。

<a id="evidence"></a>
## 2. 证据链与类型化断言

quality/query/analysis/knowledge四EvidenceEnvelope统一task/domain/scope_version/hash、来源版本/hash、完整性、上游IDs与内容hash；服务端创建ID并检查依赖无环/相同Scope。hash不是访问控制，读取重授权。截断聚合不可支持完整贡献；知识命中不等于报告正确用了必要证据。

AggregateRow和Analysis结果使用dimension_id/group_id/group_label，名称只显示；总计dimension/group为null，未知组ID __unknown__。Analysis结果单独window_index、contribution_type；外层formula_version不可含糊。Contribution Claim必须predicate=decomposition_contribution、kind=contribution、dimension_id/group_id/contribution_type/formula_version非空、window_index=null、typed_value为ratio十进制字符串；类型within/structure/entry/exit。每份证据绑定Scope，不能用全域category边际汇总支持西北category断言。

Claim固定谓词metric_value/delta/decomposition_contribution/knowledge_rule/evidence_insufficient/suggested_test；事实/贡献至少一个支持引用。完整支持键为scope_hash＋metric/version＋维度/组ID＋窗口或跨窗语义＋分量＋公式＋单位。组名同名、错分量、错公式、跨Scope、相反方向均拒绝。贡献不是因果；hypothesis写未知条件和可验证下一步，不能用“假设”标签豁免确定因果断言。

<a id="verifier"></a>
## 3. 核验与渲染

先引用存在/授权/关系/Scope/版本/完整性→计数/率/单位/舍入/贡献残差→固定谓词支持→必要证据完整→开放解释独立复核和因果硬负例→模板渲染。数值来自已核验结构化Claim；自由文本新事实/数值无法核验则拒绝发布或明确不足，不通过关键词/LLM Judge冒充通用事实证明。修正最多2语义次数并共享预算，无余额不能为了渲染再收费。

<a id="report"></a>
## 4. 报告与交互

报告含安全原问题/澄清、授权域/单地区过滤、指标/公式版本、两窗/H/as_of/业务时区/UTC口径、snapshot/水位/DQ、样本量/幅度/组内与结构/新增退出、事实/贡献/假设分层、逐Claim证据、限制/下一步、唯一终态/原因、三时钟与预算/unknown。Markdown/JSON来自同一Report对象，不能另生成矛盾数字。

CLI支持创建/进度/澄清/显式取消/报告证据/导出；等待显示queue/active/端到端与可取消状态。SSE只流脱敏进度/核验摘要，断线游标续读；无控制WS义务。错误说明缺失、影响与恢复，隐藏堆栈/他域对象。

<a id="acceptance"></a>
## 5. 验收

T06 CAL-R01仍待关闭；T07≥20植错报告覆盖错ID/同名组串维、within/structure互换、entry/exit、错公式/单位/窗口/过滤、引用/必要证据与因果变体，硬例全检出。三轮盲测支持精度≥95%/无依据≤5%/可解析100%，必要证据缺失则case失败，无断言不能假报100%。T13三名代理至少两名独立完成并查证据。当前是设计/静态核对，不是检索或报告运行通过。
