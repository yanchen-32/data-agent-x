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

## 首批业务边界样例

`tests/fixtures/order_boundaries/` 保存 3 份合成 JSON 样例及 `ORACLE.md` 独立人工推导记录，覆盖成熟期/退款水位、UTC 半开支付窗口/闭合退款观察期、重复订单阻断。成熟水位样例包含等号通过和提前 1 微秒未成熟两个控制变体。输入、业务规则、计算依据及预期结果一并保存，预期值静态填写，不调用待测代码生成。`tests/test_boundary_fixtures.py` 只验证样例完整性及预期算术一致性，不证明业务计算器、批次 DQ、SQL 或指标计算已实现；记录尚待用户独立人工复核。这里只完成首批样例，不将调查原型里程碑标记为完成。

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
