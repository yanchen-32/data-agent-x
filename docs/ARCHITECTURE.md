# DataAgentX 当前实现架构

本文描述此公开分支中已实现的基础 API 和独立订单字段校验。规划能力见 ROADMAP.md，项目边界见 PROJECT_CHARTER.md。当前开发工作区的未提交 Provider 不属于本分支。

- **最小订单字段校验**：`order_validation.py` 的 `validate_order()` 接收单行 Python 字段映射，合法时返回不可变的 `OrderRecord`，非法时抛出带字段说明的 `ValueError`。这是依据 DD02 v1.2 和 SRS §4.1 定义的局部实现，不是已冻结的外部 API 或完整导入契约。必填字符串字段为 `source_row_id/domain_id/snapshot_id/order_id/product_id/region_id/channel_id`，须非空且非纯空白；支付有效性在本实现中命名为 `is_payment_valid`，只接收布尔值，False 保留供后续规则筛选；必填 `paid_at` 只接收带时区的 `datetime` 并转 UTC，保留微秒，不解析外部 RFC3339 字符串。缺失或额外字段拒绝，`__unknown__` 维度保留，输入不被修改。本函数仅覆盖带支付时间的订单行，不处理未支付且时间为空的原始记录；不验证重复主键、单品/单次支付事实、域授权、维度目录关联、退款关系、成熟期、水位或导入批准状态，尚未接入 API/数据库。`tests/test_order_validation.py` 覆盖正常输入、非法类型/空值、缺失/额外字段、无时区时间、偏移转 UTC、False 和未知维度保留。

- **src layout**：业务包放在 `src/dataagentx/`，与项目根目录和测试分开，减少从当前目录误导入源码的问题，让开发和测试通过安装后的包访问代码。
- **pyproject.toml**：统一声明构建方式、项目元数据、Python 版本、运行与开发依赖、`dataagentx` 命令入口及 pytest 配置。
- **环境配置**：`config.py` 的 `load_settings()` 每次调用都通过标准库 `os.getenv` 读取 `DATAAGENTX_HOST` 和 `DATAAGENTX_PORT`，默认值为 `127.0.0.1` 和 `8000`，返回不可变的 `Settings` dataclass；端口转换为整数并检查 1～65535 范围，非法值抛出 `ValueError`。`main.run()` 在启动时加载配置并传给 Uvicorn。`tests/test_config.py` 使用 pytest `monkeypatch.setenv` / `delenv` 控制环境、验证默认值与覆盖、重复读取和端口校验，并替换 `uvicorn.run` 验证启动参数；monkeypatch 在测试结束时自动恢复环境和替换对象。
- **类型标注**：函数参数、返回值和容器具有明确类型，例如 `ItemService.get()` 返回 `Item | None`，提醒调用方处理查询不存在的情况；类型标注本身不执行运行时校验。
- **Pydantic**：`schemas.py` 中的 `ItemCreate` 校验请求名称长度，`ItemRead` 定义响应字段，配合 FastAPI 完成响应校验与 JSON 序列化。
- **dataclass**：`models.py` 中的 `Item` 表达内部领域数据，自动生成初始化等方法，使用 `frozen=True` 限制字段赋值；默认不校验字段类型，也不负责 HTTP 输入校验。
- **测试组织**：`tests/test_health.py` 检查健康接口状态码与响应体，`tests/test_items.py` 检查创建成功、空名称拒绝和查询不存在；二者通过 FastAPI `TestClient` 调用接口。`tests/test_service.py` 使用函数级 pytest fixture 为每个测试创建独立的 `ItemService`，直接验证初始状态、创建与查询、缺失查询、合法 ID 下界和 ID 递增，不经过 HTTP 层。运行 `.venv/bin/python -m pytest` 执行全部测试。
- **日志处理**：使用标准库 `logging`，`logging_config.py` 在根 logger 没有 handler 时添加 stdout 输出及时间、级别、模块名格式，默认级别为 INFO；业务模块通过 `getLogger(__name__)` 记录创建成功（INFO）和查询不存在（WARNING）。

## 独立参考计算

`reference/cohort.py` 的 `calculate_reference(input)` 仅使用标准库，位于生产包外，不导入 `dataagentx` 或共享生产校验工具，也不读取 Fixture 的 `expected`。它对小型合成输入独立解析 UTC 时间、构造半开支付队列、检查逐单成熟与两类水位，按订单集合去重成功退款，使用 `Fraction` 计算率及变化。前提不足时业务指标为空，候选订单另列为诊断。重复订单/事件、域快照混入、孤立或支付前退款以 `ValueError` 拒绝；这不是生产 DQ 结果映射。授权、维度目录、批准导入、SQL/数据库和贡献分解均未实现。

`reference/manual_checks/2026-10-14.md` 与 JSON 先于参考函数保存两个 Fixture 的输入驱动逐单推导及静态数值，标注输入 hash 和既有预期曾被阅读的限制；不声称首次盲审或用户独立验收。`tests/test_reference_cohort.py` 将实际参考计算与该记录、原静态预期对照，并验证水位/未成熟控制变体、重复订单拒绝、空队列阻断和输入不被修改。

同一测试文件使用 `pytest.mark.parametrize` 对 A3-04/05 固定输入调用既有参考函数，并与冻结预期核对候选订单、发布指标及变化。A3-04 的测试侧局部核验另按输入的支付有效性、半开支付窗、闭合退款观察期、as_of 和退款订单去重规则复核诊断 N/U/率，不读取参考函数结果来计算诊断，不把静态 `diagnostic_cohort_metrics` 当作参考函数已返回的字段，也不把未发布的 `metrics.N=null` 改写成0。A3-05 同时核验 `Fraction` 精确数值和类型。[初始回归记录](../reference/regression_checks/A3-04_A3-05.md) 保持原样；[参数化运行记录](../reference/regression_checks/A3-04_A3-05_parametrized.md) 保存本次命令、结果及静态文件核验信息。未扩展参考函数接口、引入框架或回填冻结预期。

`test_reference_a3_06_counts_refund_orders_not_events` 对已具备输入和人工预期的 A3-06 直接调用既有参考函数，核验同单两笔不同事件ID的成功退款只计一个退款订单、双窗候选集合、N/U/率及变化，并检查 `Fraction` 类型和 Fixture 不被修改。[A3-06 回归记录](../reference/regression_checks/A3-06.md) 保存实际运行命令、结果及冻结文件核验信息；没有将静态事件诊断当作参考函数返回值，也未修改预期或参考实现。

`reference/category_cohort.py` 的 `calculate_category_reference(input)` 新增最小类别分组参考计算，仅依赖标准库和既有总体参考函数，不导入生产业务包或读取 `expected`。它复用总体参考函数的候选队列、输入检查和比较前提，保持 `reference/cohort.py` 不变；再按订单/退款复合键重建成功退款订单集合，通过 `(domain_id,snapshot_id,product_id)` 关联产品，以类别ID归组。类别目录只补展示名，同名ID不合并；所有输入订单的产品关联先核验，缺失产品复合键抛出带订单及来源定位的 `ValueError`；只有合法产品的非关键类别ID缺失归入 `__unknown__`，已知ID无展示名时保留ID，目录重复键或域/快照混入抛出 `ValueError`。结果保留总体字段，另返回率为 `Fraction` 的 `aggregate_rows` 及两种订单归组台账；每窗只输出有候选订单的类别，总计身份字段均为空，前提阻断时不发布聚合行。`tests/test_reference_category_cohort.py` 对照 A3-07 冻结四条类别行及两条总计行，验证来源追溯、互斥穷尽、N/U汇总、精确比率和关键控制变体。[运行记录](../reference/regression_checks/A3-07_category.md) 单独保存；未接入生产SQL、正式序列化、授权、批准导入或贡献分解，不将共享总体前提说成两套独立总体算法。

A3-08 当前输入为修订v2：`08_category_entry_exit.json` 使用新快照、八笔支付和六笔有效退款，A两窗共享且退款率0→1、支付占比1/2→1/4，B仅基期、C仅当前且二者均有有效退款。来源与先行静态数值保存在 `reference/manual_checks/A3-08_v2.json/.md`，缺席组不补行，成熟水位、唯一复合键和分组N/U汇总由静态检查核对。另在 `reference/manual_checks/A3-08_v2_expected.json/.md` 保存仅据input逐单推导的预期后，实际调用既有类别参考函数，六条聚合行及总计变化与冻结expected全部一致；该记录包含可复现命令与hash。旧六单输入原字节保存在 `08_category_entry_exit.v1.json`；四项原计算回归仍绑定v1及原SHA-256，旧手填JSON不改。v2已增加四项专门pytest计算回归，绑定先行冻结哈希，复用既有辅助函数核对六行精确结果、来源、生命周期与守恒，并逐项检查输入及预期不变；v1原四项保持不变且通过，运行证据见 `reference/regression_checks/A3-08_v2.md`。仍待用户独立人工验收，不将v1通过记录冒称v2验收；本阶段未实现贡献分解，也未更新路线图完成状态。

## 首批业务边界样例

`tests/fixtures/order_boundaries/` 保存 10 个主合成 JSON 样例及 A3-08 v1 冻结历史副本及 `ORACLE.md` 独立人工推导记录，覆盖成熟期/退款水位、UTC 半开支付窗口/闭合退款观察期、重复订单阻断、单窗口分母为零、单地区过滤、同单多笔成功退款、同名不同ID类别分组、类别共享/新增/退出、合法产品关联下的非关键未知类别保留及缺失关键产品关联阻断。成熟水位样例包含等号通过和提前 1 微秒未成熟两个控制变体。零分母样例分别记录未发布的比较指标和人工队列诊断；地区样例同时保存被排除来源行及漏过滤反例；A3-06 保存不同事件ID的合格退款事件集合与退款订单集合，两窗事件数同为2而U分别为1和2，区分正常多次退款与重复事件ID异常。A3-07 保存两个同名类别的独立ID、产品复合键关联、分组来源台账，以及双窗各两条类别行和一条总计行；每窗分组N/U汇总等于总计，展示名不作身份键。输入、业务规则、计算依据及预期结果一并保存，预期值静态填写，不调用待测代码或参考函数生成。`tests/test_boundary_fixtures.py` 只验证样例完整性、来源关联、事件诊断与订单计数及预期算术一致性；A3-07 另核对静态分组身份、来源互斥穷尽、汇总以及输入的成熟与水位约束，不证明业务计算器、批次 DQ、SQL 或分组计算已实现，未扩展参考函数。记录尚待用户独立人工复核。这里只完成首批样例，不将调查原型里程碑标记为完成。

A3-07 另有四项按“支付窗 × 类别ID”参数化的来源追溯检查，使用人工固定的订单和退款来源行台账，与原始输入的复合订单键关联、静态组身份及N/U/率核对，覆盖两个无退款组。该检查只验证这一合成样例的一致性，不实现通用退款筛选或分组计算；创建阶段的待补清单在 `ORACLE.md` 中保留为历史，2026-10-21 新增的分组参考计算覆盖另行记录。

A3-09 `09_unknown_category_preserved.json` 固定八单五退款，两窗同时包含已知类别及非关键未知类别。订单完整关联同域/快照的唯一产品，只有product_unknown的category_id为null；未知组身份为(category,__unknown__)，不以产品关联失败制造未知。先行逐单依据见 `reference/manual_checks/A3-09.md`；静态检查核对窗口、成熟水位、唯一复合键、退款来源及分组N/U守恒。两窗总率的先行预期为1/2→3/4，已知/未知组退款率不同。现已先保存 `reference/manual_checks/A3-09_expected.json` 独立台账，再新增一项固定计算回归，绑定Fixture、台账和input指纹；从input调用既有类别参考函数，对照六行精确Fraction、总计变化、来源及守恒，并核对输入/预期与文件未变。冻结及实际输出见 `reference/regression_checks/A3-09.md`，不改创建阶段记录或既有未知变体；未实现关键产品关联异常的生产DQ映射。

A3-10 `10_missing_product_join_blocks.json` 新增四笔支付、两笔合法退款，仅当前窗J10-C2 / r10-row-c2缺失产品复合键关联。独立说明和来源台账保存在 `reference/manual_checks/A3-10.md/.json`，先行预期为blocked_by_quality，两窗发布指标及变化均null、无聚合行或归组台账，不降级成unknown。静态检查核验唯一故障、来源和其余时间/成熟水位/键约束均合法。现已新增固定拒绝回归，先确认真实红灯后定点修复：参考层在比较门槛之前拒绝任一输入订单缺失产品复合键，不再降级unknown；合法category_id=null与已知ID缺展示名仍保留。旧missing=product变体更正为ready/immature拒绝测试，来源及实际输出见 `reference/regression_checks/A3-10.md`。冻结Fixture与原独立台账不改；当前以ValueError拒绝，不是生产blocked_by_quality状态映射，未验收生产DQ。

## 订单字段的依据与校验边界

当前有效契约为 DAX-RB-1.2.1 清单中的 DD02 v1.2、SRS v1.2 和对象 Schema v1.2.1。对象 Schema 的 26 个定义描述调查接口和证据，尚无 `OrderRecord` 或原始 `orders` 行定义；本地结构不等于已冻结的订单导入 Schema。函数只使用标准库，不在运行时加载设计文件。

| 字段 | 当前单行校验 | 依据 |
| --- | --- | --- |
| `source_row_id` | 必填、非空且非纯空白字符串 | DD02 §1 的原始来源追溯；字符串类型是局部实现约定 |
| `domain_id`、`snapshot_id` | 必填、非空且非纯空白字符串，最多 256 字符 | DD02 的域/快照隔离语义；共享标识长度与有效 `ScopeSpec` 的 `minLength=1/maxLength=256` 一致 |
| `order_id`、`product_id`、`region_id`、`channel_id` | 必填、非空且非纯空白字符串 | SRS §4.1 的订单语义；字符串类型是局部实现约定 |
| `paid_at` | 必填、带时区的 Python `datetime`；转 UTC 并保留微秒；转换超出可表示范围时抛出 `ValueError` | DD02 的必需支付时间及时间规范化语义；不实现外部 RFC3339 字符串解析 |
| `is_payment_valid` | 必填、严格布尔值，False 保留 | SRS 的支付有效性语义；字段名和布尔类型是局部实现约定 |

校验顺序为映射类型、字段完整性、额外字段、ID 类型与长度、支付时间、布尔值、UTC 转换；合法时构造不可变 `OrderRecord`，输入不被修改。`tests/test_order_validation.py` 分别验证正常输入、缺失必填字段、非法字段值，并覆盖 256/257 字符、UTC 日期上下界、整数 0/1 不能替代布尔值，以及已有 tzinfo 但实际偏移为空的时间。`__unknown__` 标识保留不等于验证过维度目录；单行字段校验不证明授权、唯一性、退款关联、成熟期、水位或批准状态已通过。
