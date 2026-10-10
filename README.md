# DataAgentX

Evidence-Grounded Business Data Investigation Agent：面向成熟历史退款队列的证据调查项目。

本公开版本对应设计基线DAX-RB-1.2.1，提供需求、DD01–DD08、机器契约与可复跑设计核对。应用源码沿用先前冻结的基础FastAPI快照：健康检查和内存items接口；调查Agent、真实PG、Runtime与真实Provider尚未验收。当前开发中的未提交Provider代码不纳入此发布。设计版本v1.2.1与pyproject中的基础应用版本0.1.0分别表示设计基线和应用状态。

从[当前工程基线](docs/engineering/BASELINE.md)、[项目章程](docs/PROJECT_CHARTER.md)、[里程碑](docs/ROADMAP.md)和[实际架构](docs/ARCHITECTURE.md)开始阅读。需求维持25 Must、6 Should、3 Could。本次维护包含DD07体验走查措辞、固定17份当前技术Markdown扫描范围，以及全部公开文件的本机信息脱敏。独立设计ZIP不含应用源码；本GitHub快照额外保留基础src/tests。

Python 3.10及以上，在项目根目录安装并运行基础API：

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
python -m pytest
dataagentx
```

先激活所创建的虚拟环境再执行安装命令。启动默认127.0.0.1:8000，可通过DATAAGENTX_HOST与DATAAGENTX_PORT覆盖；端口须为1至65535的整数。接口为GET /health、POST /items、GET /items/{item_id}。

设计契约核对需要另行安装jsonschema，然后运行：

```bash
python "docs/engineering/05_原型验证与实现/DataAgentX_v1.2.1契约边界核对.py" --root .
```

公开冻结基础API的22项现有测试全部通过，并已确认导入本快照源码，见[基础API核对](verification/基础API核对.json)。本次设计核对固定125项全部通过，详见[结果](verification/契约与独立参考核对.json)和[维护记录](verification/公开维护核对.json)。内部旧独立包116项与完整归档125项均通过，旧记录保留；新脚本的17份固定文档清单使结果不再受归档数量影响。以上属于静态契约及独立语义参考核对，不能替代应用集成验收。

## 订单字段校验

公开分支新增独立函数 `validate_order(data)` 和不可变对象 `OrderRecord`，详见[代码](src/dataagentx/order_validation.py)与[测试](tests/test_order_validation.py)。输入为单行 Python 字段映射：七个来源/域/快照/订单/维度 ID 必须是非空字符串，`paid_at` 必须是带时区的 `datetime`，`is_payment_valid` 必须是布尔值。缺失、额外及非法字段抛出 `ValueError`；时间统一转 UTC，输入不被修改，False 和 `__unknown__` 保留。

本函数不校验批次唯一性、域权限、维度关联、退款关系、成熟期或水位，尚未接入调查 API。订单校验新增 27 项测试；本次公开分支的基础 API 与订单校验全量测试共 49 项通过，见[核对记录](verification/订单校验核对.json)。开发目录的 Provider 及其 5 项测试未纳入本分支。

公开清单见[RELEASE_MANIFEST](RELEASE_MANIFEST.json)。本分支不携带内部原始材料、个人计划、环境日志或旧 Git 历史。标签 `dax-public-v1.2.1` 冻结独立根提交的设计及基础 API 快照；分支 `release/public-v1.2.1` 在该公开历史上继续提交订单校验，既有标签保持不变。下一步建设固定数据/Oracle、真实 PG 最小权限与第一条可复算证据报告。
