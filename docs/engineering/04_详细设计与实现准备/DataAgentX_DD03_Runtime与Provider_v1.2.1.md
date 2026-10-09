# DD03 Runtime与Provider v1.2.1

日期：2026-10-09；基线DAX-RB-1.2.1。状态：设计规格已修订，应用实现/运行验收待完成。控制依据：[SRS v1.2](../01_需求基线/DataAgentX_SRS_v1.2.md)。本版仅修订已回答澄清后的调度/计时及关联无Scope终态摘要，其余v1.2设计不变；本文件完整替代DD03 v1.2实施指导。

<a id="runtime"></a>
## 1. 组件与流程

单Python进程，Python3.10兼容受监督asyncio任务。Supervisor持活动任务强引用和有限队列；Planner只出结构化Action；Registry/Executor检类型、权限、范围和额度；BudgetLedger原子预留/结算；DispatchGate关闭新发；TaskRepository短事务CAS；Verifier/Renderer只发布已核验事实。各模块可替换协议，不建分布式调度/租约服务。

流程：鉴权/持久受理→就绪队列→范围解释/澄清→冻结Scope→DQ→必要工具计划/SQL/知识/分析→核验→唯一终态。单任务工具串行，后台不阻塞查询/取消。八公开状态保持，queued仅phase。无异常且证据充分completed；数据/必要证据不足insufficient_evidence；技术不可恢复failed；执行/调用预算耗尽budget_exceeded；显式取消cancelled。SSE仅观察，断开不取消；WS恢复SC-01默认关。

<a id="timing"></a>
## 2. 三类时钟与队列

| 计时 | 累计范围 | 上限/行为 |
| --- | --- | --- |
| Queue Waiting | 任务就绪但等待执行槽；首次从持久受理accepted_at开始，澄清后可再入队 | 累计≤30秒；到界关闭发送，failed/QUEUE_WAIT_TIMEOUT；尚未执行者零模型/工具费用 |
| Active Execution | 持执行槽期间的解析/模型/工具/网络等待/重试/退避/分析核验 | 累计≤120秒；到界关闭发送并budget_exceeded/ACTIVE_DEADLINE_EXCEEDED |
| Clarification Wait | needs_clarification且phase=awaiting_user等待人工，释放槽；充分有效答案持久接受时结束本段 | 全任务累计≤1800秒，到界failed/CLARIFICATION_EXPIRED；不清零已用queue/active/次数/Token |
| End-to-End | accepted_at至最终terminal_at墙钟；未终态取当前 | 包含前三者与有界收尾，单列观测；外部远端残余单独审计，不宣称120秒端到端SLA |

使用单调时钟计持续时间，UTC保存事件锚点；重启非终态failed/PROCESS_RESTARTED、不重放。所有入/出队、持槽、澄清、关入口/终态时间持久记录，防计时漏段。active_elapsed_ms账本必须等于TimingView.active_execution_ms，queue不占Token/active，不因重入重置。边界用>=判到界，调度tick和终态收尾误差单列实测，不能向下截断违规。

设计默认1执行槽、16队列、每主体未终态≤16；容量事务准入，满在创建前429、暂停/依赖不可用503，无task和调用。已受理到期不是HTTP429，而是可查询失败终态。澄清答案按字段/权限/必需条件由服务端核验：非法400不改变任务；合法部分答案可200并继续awaiting_user、保留尚缺字段；有效且充分的答案与当前澄清关闭、累计人工等待结算、ready_since_at和pending_requeue事件同事务提交，然后200 TaskView。兼容公开status=needs_clarification，内部phase=pending_requeue、clarification=null，界面显示“答案已接受，等待系统调度”，不能要求用户重复提交。排队是否满不影响这次接受，不返回REQUEUE_CAPACITY。

从充分答案持久接受时开始计累计Queue Waiting（即使实际就绪队列尚无空位），暂停人工时钟；重新持槽才计Active，已耗queue/active/工具/Token不清零，pending_requeue同样受原累计30秒上限。到界failed/QUEUE_WAIT_TIMEOUT，不能误报CLARIFICATION_EXPIRED。无效/部分答案没有完成用户责任，仍用人工等待账。

Supervisor自动从既有任务记录发现pending_requeue，以首次ready_since_at/task_id和普通就绪任务作公平调度，不依赖客户端重发或新增后台模型调用。pending_requeue不增建任务、不释放原主体非终态配额；候选限于有限登记主体和原每主体上限，并披露pending数量/等待，不作为隐藏无界队列或绕过创建容量。实际就绪队列仍≤16；待重入容量和队列配置合理性由原CAL-P01校准。答案接受/入队/超时/取消均用state_version CAS，取消关闭入口时phase先转cancelling；已超时/终态不能再调度。

同clarification_id、同答案重试仅返回既有接受结果/当前TaskView，不重置ready_since_at、不产生第二次排队；异答案409，已接受答案的幂等查询先于旧expected_version拒绝。pending取消/重启仍遵守唯一终态、不重放与原预算。先允许幂等重放旧结果，再判新容量，防满队列时旧key误429。

<a id="budget"></a>
## 3. 本地账本与取消

工具≤12、模型≤8、SQL≤10秒/1000行。audited默认全输入估算累计预留≤20000、请求输出cap累计≤4000，所有system/tool schemas/历史/结果纳计；外部实际usage/隐藏Token不宣称严格上界。strict_calibrated仅有独立真实计数上界证据才可启用。known/unknown/pending/估算/实际差异分层；已发未知占额不记0，已证未发可释放。真实超额必须写账、标差异并阻止下一发，不能用DB CHECK丢弃证据。

validate→短事务reserve→进DispatchGate重查状态/取消/auth/scope/queue/active→Adapter可观测实际begin/登记call→出gate等待→结算/核验。网络等待不持协调锁。发送前取消的已证未发预留释放；终态后零新调查发送，迟到结果只审计。取消受理关闭入口≤2秒、本地编排≤5秒、服务器SQL≤10秒；完成/取消/期限竞争首先CAS成功者唯一终态，失败者仅审计/清理。

<a id="provider"></a>
## 4. Provider与有界恢复

协议estimate_input/prepare_request/begin/await_result/abort_local/normalize_response。Mock脚本可注入非法JSON/Schema、超时、未发失败、已发未知/迟到及usage差异；真实替换不改核心。小样本audited先绑定provider/model/估算方法/请求输出cap/usage和取消能力、带日期价格与运行级次数/费用停止规则；不因无法证明严格计费上界永久停在Mock，也不允许未知费用无限批量。

上下文固定安全/动作契约→Scope/目录→必要证据→短决策历史→问题；只能压缩非必要重复，不能丢授权/口径/DQ。权限拒绝不重试；明确暂时失败初次+最多2重试，退避候选0.25/0.5秒计active；全任务语义修正最多2次，均共享总账。坏数据不投票放行，内部契约坏/重启failed，任务最终状态与原因明确。

<a id="verification"></a>
## 5. 验证责任

T04并发CAS/幂等和Fake替换；T09六故障×≥5；T10≥20取消＋≥20界限，补排队到界/澄清暂停后重入/已耗active/首次未执行零调用/取消与超时同刻。T11全调用/时钟/usage追溯；T15 CAL-P01防快速拒绝取巧。当前只做契约与独立时钟参考核对；真实asyncio、DB、Provider取消尚待实测。

补充T04/T10边界：排队中Scope=null立即取消、澄清前取消、范围解析失败；充分答案遇满队列200且自动重入、重复提交不重复计时、答案接受与人工到期/取消竞争、pending累计队列到界。仅契约/参考模型核对不证明真实Supervisor或PG事务已通过。
