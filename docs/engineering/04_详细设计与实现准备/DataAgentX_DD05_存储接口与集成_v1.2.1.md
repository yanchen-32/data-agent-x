# DD05 存储接口与集成 v1.2.1

日期：2026-10-09；基线DAX-RB-1.2.1。状态：设计规格已修订，应用实现/运行验收待完成。控制依据：[SRS v1.2](../01_需求基线/DataAgentX_SRS_v1.2.md)。本版完整替代DD05 v1.2，仅更新终态摘要和澄清自动重排队，其他设计沿用。

<a id="storage"></a>
## 1. 存储边界与模型

一个PostgreSQL实例，business/app_state两个数据库和分离凭据；业务查询身份不能连接应用库，迁移/导入角色离线，不传模型。单进程持执行权，短事务不跨网络等待。

| 表 | 必要字段和约束 |
| --- | --- |
| tasks | UUID、principal/domain/auth_version、受控request、八状态/phase/state_version、scope_version、cancel_requested、accepted/started/terminal时间、累计queue/active/clarification、config_hash、内部deleting；计时违规也要记录，不用CHECK上界丢证据 |
| task_scopes | task_id+scope_version唯一、不可变Scope JSON/hash含filters；跨范围旧证据禁止移用 |
| clarifications | task/clarificationID、expected_state_version、字段/答案hash、累计等待、到期、result_scope_version；同答案幂等/异答案409；充分答案接受即结清人工等待，ready_since_at和pending_requeue持久化；系统自动调度 |
| budget_ledgers / calls | 同task原子预留，次数/known/unknown/pending、实际/估算；call UUID、logicalID+attempt唯一、dispatch/deadline/outcome、scope/version、usage允许null且unknown显式 |
| evidences / reports | task/scope复合关系、来源/上游/hash/完整性/结构化Claim；partial unique保证每task至多一个final报告 |
| events | task+event_seq，状态版本/脱敏内容/UTC与持续时间；同事务outbox，清理后允许序号空洞 |
| idempotency | principal/operation/key_hash唯一、canonical_request_hash、result_ref、24h到期、deleted_marker；同key异请求409，不因清正文重复计费 |
| manifests / evaluation_archives | 冻结snapshot/catalog/index/规则与生成器版本水位；正式run用途/域/所有者/sealed时间/180天到期、全文件hash和读回/重评分证明 |

诊断日志不存原始问题/参数，受控任务对象只存允许业务字段；API不提供原始Provider提示/响应下载。普通7/30天与正式run封存180天分开，细则见本版DD01。正式归档生成过程需原子临时目录→hash验证→sealed登记，失败禁止相关普通TTL误删；失败run也归档，不只成功结果。

<a id="canonical"></a>
## 2. 时间规范、Scope与幂等hash

外部Z/±HH:MM RFC3339（0–6小数）先严格解析真实日期/偏移，拒绝无偏移、-00:00、闰秒；转换UTC固定6位小数Z。business_timezone显式保留，不能覆盖输入偏移。每window start<end，保持基期/当前语义顺序；退款≤支付、成熟/水位等跨字段关系由服务端校验。

规范JSON：UTF-8、ensure_ascii=false、键排序、无空白、禁止NaN；时间统一微秒Z，Decimal去尾零/负零归零，集合dimensions排序去重（输入重复拒绝），region_ids按已核验ID列表（0或1），窗序保留。scope_hash输入排除scope_hash自身和分配型scope_id/scope_version，包含schema_version、domain、全部业务字段filters、snapshot/知识版本hash和水位；scope_id/version另作不可变关系验证。于是相同主体域/输入语义不同外部offset产生相同业务scope_hash，改变地区/窗口/H/版本必须不同。

幂等request_hash在认证后、容量前计算：允许字段、保持question原文（不做语义改写）、显式登记默认（filters=[]/control_mode=explicit_cancel，默认未授权则不填）、windows/as_of同时间规范、dimensions排序；requested_scope_id映射当前域与授权版本纳上下文。不存在等价的question措辞不强行视为同请求；仅hash时间等价不改变权限。key不作为业务字段，principal/operation纳唯一键。跨版本规范算法需保存canonicalization_version防旧key行为改变。

<a id="transactions"></a>
## 3. 原子性与重启

创建鉴权/Schema/规范hash→先查24h幂等旧结果→容量事务插入task/ledger/首queued事件→提交后202；无DB返回503不发虚构task。动作预留与gate见DD03；完成/取消/期限CAS同事务写唯一终态、可表示真实口径状态的final报告与事件，首终态获胜。若尚无冻结Scope：非completed终态可写ReportView状态摘要，scope_hash=null、claims=[]、evidence_refs=[]、非空limitations，质量栏写“尚未建立调查口径/未执行质量核验”，Markdown仅已知状态、原因、时间/预算、恢复条件，不作业务结论；insufficient_evidence在Scope前也统一采用该摘要，不仅返回Task状态。若有Scope，report.scope_hash必须等于本任务真实冻结Scope的hash，不能捏造形式合法值；completed的Task.scope与report.scope_hash必须真实存在且一致，Verifier核验必需Claims/证据后发布。无Scope摘要用状态/关系/空业务证据验证路径，不要求伪造口径才能原子提交。数据库不可用不能预先承诺终态持久成功。澄清核验当前ID/expected_version/答案，服务端授权后才新Scope；未冻结前可补字段，冻结后改地区创建新任务。充分有效答案接受与澄清关闭、停止本段人工时钟、ready_since_at及pending_requeue事件同事务，200 TaskView，Scope若已完整合法同时冻结；队满由Supervisor自动等待/重入并计原累计queue，不要求用户重复答复。合法部分答案仍awaiting_user，非法答案400。重复同答案先查已接受记录、返回既有结果，不重复排队；异答案409。

重启扫描旧非终态failed/PROCESS_RESTARTED，已发未知保留unknown，不重放。当前授权/内部deleting每步/每读重检。SSE提交后通知，丢通知按event_seq补读；旧游标超保留范围409 EVENT_CURSOR_EXPIRED，客户端取Task快照再订阅，不把缺段流冒充完整历史。

<a id="api"></a>
## 4. 当前API与对象

实现契约为[Schema v1.2.1](DataAgentX_对象Schema_v1.2.1.json)、[OpenAPI v1.2.1](DataAgentX_API契约_v1.2.1.openapi.json)、[配置 v1.2.1](DataAgentX_合成运行配置_v1.2.1.json)。OpenAPI3.1、JSONSchema2020-12；未知字段拒绝，shape不证明权限/数值/时间语义。

| 方法路径 | 成功与限制 |
| --- | --- |
| POST /v1/investigations | 202 TaskView；question非空≤4096字符、body≤64KiB；可选filters.region_ids、带偏移windows/as_of、登记scope映射；Idempotency-Key≤128字符；不接受principal/domain授权自赋 |
| GET /v1/investigations/{task_id} | 200 TaskView，scope可null；含TimingView、budget/状态/原因/澄清/限制 |
| POST /v1/investigations/{task_id}/clarifications | 200 TaskView异步继续；clarificationID+expected_version+非空answers；旧问题/异答案409；充分答案200、pending_requeue自动调度，不用容量429要求用户重答 |
| POST /v1/investigations/{task_id}/cancel | 202受理清理；已有终态200原结果，幂等/唯一终态竞争 |
| GET /v1/investigations/{task_id}/events | 200 text/event-stream；Bearer、游标、已核验/脱敏事件，断开不取消 |
| GET /v1/investigations/{task_id}/report | 200 ReportView或text/markdown；无Scope终态为null-scope状态摘要，completed须真实Scope；未就绪409、格式不支持406 |
| GET /v1/investigations/{task_id}/evidence/{evidence_id} | 200 EvidenceEnvelope；重检task/Scope/domain/主体关系，跨关系404 |

共7路径、7HTTP操作；无公开DELETE/控制WS。统一ErrorEnvelope：request_id和error{code,message,retryable,details白名单}；400Schema/格式，401身份，403明确未授权范围，404他人对象，409状态/幂等/游标，413正文，429容量，503依赖，500脱敏内部错。旧/items的422保持，不借设计破坏基础示例行为。

<a id="integration"></a>
## 5. 交联与实现入口

IF01 HTTP/SSE/CLI→身份/幂等/取消；IF02业务DB→Scope参数化只读模板/证据；IF03受信知识CLI→版本有效期；IF04Mock/真实Provider→有界调用审计；IF05有界聚合→确定性贡献；IF06 Memory协议默认关；IF07公开runner/私有scorer隔离。建议api/catalog/runtime/tools/sql/retrieval/analytics/verification/storage/evaluation边界，无需拆服务。旧ItemService不是调查状态库，ARCHITECTURE只更新实际已实现部分。

先固定fixture＋独立Oracle→成熟窗/单地区×维度贡献→最小真实PG只读/两域→离线核验报告→Mock状态/取消→真实小样本。T04/T08/T10/T11/T13真实PG事务/竞争/重启/TTL/取消与Provider证据仍待完成；本轮不以Schema通过代替实现。

T04/T10须覆盖null-scope取消/队列超时/解析失败/Scope前不足摘要、completed空Scope拒绝、伪造hash关联拒绝、澄清满队200/自动调度/CAS竞争。Schema仅检查shape；真实task/scope/报告引用需运行服务端验证。
