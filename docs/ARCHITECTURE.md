# DataAgentX Architecture Note

This document describes the system as it is currently implemented. Planned capabilities belong in `ROADMAP.md`; project goals and boundaries belong in `PROJECT_CHARTER.md`.

- **src layout**：业务包放在 `src/dataagentx/`，与项目根目录和测试分开，减少从当前目录误导入源码的问题，让开发和测试通过安装后的包访问代码。
- **pyproject.toml**：统一声明构建方式、项目元数据、Python 版本、运行与开发依赖、`dataagentx` 命令入口及 pytest 配置。
- **环境配置**：`config.py` 的 `load_settings()` 每次调用都通过标准库 `os.getenv` 读取 `DATAAGENTX_HOST` 和 `DATAAGENTX_PORT`，默认值为 `127.0.0.1` 和 `8000`，返回不可变的 `Settings` dataclass；端口转换为整数并检查 1～65535 范围，非法值抛出 `ValueError`。`main.run()` 在启动时加载配置并传给 Uvicorn。`tests/test_config.py` 使用 pytest `monkeypatch.setenv` / `delenv` 控制环境、验证默认值与覆盖、重复读取和端口校验，并替换 `uvicorn.run` 验证启动参数；monkeypatch 在测试结束时自动恢复环境和替换对象。
- **类型标注**：函数参数、返回值和容器具有明确类型，例如 `ItemService.get()` 返回 `Item | None`，提醒调用方处理查询不存在的情况；类型标注本身不执行运行时校验。
- **Pydantic**：`schemas.py` 中的 `ItemCreate` 校验请求名称长度，`ItemRead` 定义响应字段，配合 FastAPI 完成响应校验与 JSON 序列化。
- **dataclass**：`models.py` 中的 `Item` 表达内部领域数据，自动生成初始化等方法，使用 `frozen=True` 限制字段赋值；默认不校验字段类型，也不负责 HTTP 输入校验。
- **测试组织**：`tests/test_health.py` 检查健康接口状态码与响应体，`tests/test_items.py` 检查创建成功、空名称拒绝和查询不存在；二者通过 FastAPI `TestClient` 调用接口。`tests/test_service.py` 使用函数级 pytest fixture 为每个测试创建独立的 `ItemService`，直接验证初始状态、创建与查询、缺失查询、合法 ID 下界和 ID 递增，不经过 HTTP 层。运行 `.venv/bin/python -m pytest` 执行全部测试。
- **日志处理**：使用标准库 `logging`，`logging_config.py` 在根 logger 没有 handler 时添加 stdout 输出及时间、级别、模块名格式，默认级别为 INFO；业务模块通过 `getLogger(__name__)` 记录创建成功（INFO）和查询不存在（WARNING）。
