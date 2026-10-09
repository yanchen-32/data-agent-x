# DAX-RB-1.2.1 当前工程基线

日期2026-10-09。设计契约补丁发布，实际工程验收待完成。本版只修正无Scope终态摘要、充分澄清答案后自动重排队/计时、实际完成吞吐三项；需求与架构主线保持。SRS/优先级v1.2及本次三项需求补充共同定义需求，受影响DD03/DD05/DD06与机器契约已提供完整v1.2.1。

下列是唯一有效文件及准确版本，未修改模块继续v1.2，不要用“所有文件必须最新后缀”推定生效。旧版规格保留于内部归档，不随公开包提供。公开包以本清单列出的当前技术文件为准。

- [DataAgentX_SRS_v1.2.md](01_需求基线/DataAgentX_SRS_v1.2.md)（1.2）
- [DataAgentX_需求优先级清单_v1.2.md](01_需求基线/DataAgentX_需求优先级清单_v1.2.md)（1.2）
- [DataAgentX_需求评审记录_v1.2.md](01_需求基线/DataAgentX_需求评审记录_v1.2.md)（1.2）
- [DataAgentX_总体设计方案_v1.2.md](02_总体设计与方案验证/DataAgentX_总体设计方案_v1.2.md)（1.2）
- [DataAgentX_指标目录与数据契约_v1.2.md](02_总体设计与方案验证/DataAgentX_指标目录与数据契约_v1.2.md)（1.2）
- [DataAgentX_设计总册与完成性评审_v1.2.1.md](02_总体设计与方案验证/DataAgentX_设计总册与完成性评审_v1.2.1.md)（1.2.1）
- [DataAgentX_设计追溯矩阵_v1.2.1.json](02_总体设计与方案验证/DataAgentX_设计追溯矩阵_v1.2.1.json)（1.2.1）
- [DataAgentX_API契约_v1.2.1.openapi.json](04_详细设计与实现准备/DataAgentX_API契约_v1.2.1.openapi.json)（1.2.1）
- [DataAgentX_DD01_身份权限与生命周期_v1.2.md](04_详细设计与实现准备/DataAgentX_DD01_身份权限与生命周期_v1.2.md)（1.2）
- [DataAgentX_DD02_指标数据与SQL工具_v1.2.md](04_详细设计与实现准备/DataAgentX_DD02_指标数据与SQL工具_v1.2.md)（1.2）
- [DataAgentX_DD03_Runtime与Provider_v1.2.1.md](04_详细设计与实现准备/DataAgentX_DD03_Runtime与Provider_v1.2.1.md)（1.2.1）
- [DataAgentX_DD04_检索证据与报告_v1.2.md](04_详细设计与实现准备/DataAgentX_DD04_检索证据与报告_v1.2.md)（1.2）
- [DataAgentX_DD05_存储接口与集成_v1.2.1.md](04_详细设计与实现准备/DataAgentX_DD05_存储接口与集成_v1.2.1.md)（1.2.1）
- [DataAgentX_DD08_增强功能与扩展设计_v1.2.md](04_详细设计与实现准备/DataAgentX_DD08_增强功能与扩展设计_v1.2.md)（1.2）
- [DataAgentX_合成运行配置_v1.2.1.json](04_详细设计与实现准备/DataAgentX_合成运行配置_v1.2.1.json)（1.2.1）
- [DataAgentX_对象Schema_v1.2.1.json](04_详细设计与实现准备/DataAgentX_对象Schema_v1.2.1.json)（1.2.1）
- [DataAgentX_v1.2契约参考样例.json](05_原型验证与实现/DataAgentX_v1.2契约参考样例.json)（1.2）
- [DataAgentX_首批原型用例目录_v1.2.json](05_原型验证与实现/DataAgentX_首批原型用例目录_v1.2.json)（1.2）
- [DataAgentX_DD06_评测与验收设计_v1.2.1.md](06_评测与验收/DataAgentX_DD06_评测与验收设计_v1.2.1.md)（1.2.1）
- [DataAgentX_DD07_部署运维与交付设计_v1.2.1.md](07_发布与求职材料/DataAgentX_DD07_部署运维与交付设计_v1.2.1.md)（1.2.1）
- [DataAgentX_求职能力与工程证据矩阵_v1.2.md](07_发布与求职材料/DataAgentX_求职能力与工程证据矩阵_v1.2.md)（1.2）
- [DataAgentX_需求补充与变更记录_v1.2.1.md](01_需求基线/DataAgentX_需求补充与变更记录_v1.2.1.md)（1.2.1）
- [DataAgentX_设计发布说明_v1.2.1.md](07_发布与求职材料/DataAgentX_设计发布说明_v1.2.1.md)（1.2.1）
- [DataAgentX_v1.2.1契约边界核对.py](05_原型验证与实现/DataAgentX_v1.2.1契约边界核对.py)（1.2.1）
- [DataAgentX_v1.2.1边界用例.json](05_原型验证与实现/DataAgentX_v1.2.1边界用例.json)（1.2.1）

null-scope非completed终态发布空业务Claim/证据的状态摘要，completed必须真实Scope；充分有效答案200接受即停人工等待，pending_requeue由系统自动调度并计原累计queue30秒；完成吞吐只按测量窗内completed提交，接收队列截止前完成率单列，排空完成不计吞吐。八公开状态/26定义/7路径7操作、34需求25-6-3、原预算/取消硬门槛保持。载荷版本仍1.2，契约文档版本1.2.1，未声称旧客户端已验证兼容。

CAL-R01/CAL-P01、真实PG/Runtime/Provider和正式评测尚未验收。核对脚本只验证Schema和独立语义时间线。公开设计包不包含开发工作区状态、内部同步日志或原始资料。

技术文件位于docs/engineering，SYNC_MANIFEST列出当前文件及SHA-256。下一步固定数据/Oracle/真实PG与第一条可复算报告，不再整体重构设计。

DD07修正配置引用与体验走查措辞，不改变部署语义。公开维护同时固定核对脚本的17份当前技术Markdown扫描范围；旧内部116/125项结果保留，新结果独立记录。
