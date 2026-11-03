# A3-11：渠道固定预期与来源回归（C01/C02）

日期：2026-11-03。结论：**C01与C02共3项实际计算回归通过，结果与先行冻结预期一致；Fixture及独立expected未修改。** 本轮同时补齐执行固定回归所必需的最小渠道参考函数，不修改生产Runtime或总体/类别函数。

## 实现起点与责任

本轮开始时reference/channel_cohort.py不存在，已发布[实施方案](../manual_checks/A3-11_channel_oracle_plan.md)、[起点检查](../manual_checks/A3-11_implementation_start.md)及[冻结审核](../manual_checks/A3-11_freeze_review.md)仍作为先行依据。先新增tests/test_reference_channel_cohort.py，固定既有四项指纹并直接调用拟定接口，再新增reference/channel_cohort.py使回归可执行。

calculate_channel_reference()只接收input，调用既有calculate_reference()复用队列、成熟/水位和总体指标；独立扫描原始退款、按订单去重，与过滤后的队列相交，再直接按订单channel_id分组。目录使用完整复合键、产品关联覆盖全部原始订单，校验先于不足返回；未知渠道拒绝是参考输入范围限制，不等于业务关键DQ。来源与完整质量诊断只在测试端核对，不伪造正式API/DQ/QueryEvidence返回字段。

## 本轮新增回归与实际值

| 对应方案 | 测试 | 实际核对范围 |
| --- | --- | --- |
| C01 / 1项 | test_channel_reference_a3_11_matches_six_frozen_rows_and_metrics | 只传input，六条行、身份/label、整数计数及Fraction、总体变化；先查原列表长度/键唯一性，再逐行比较独立expected；原总体字段与既有函数一致仅作复用检查 |
| C02 / 2项 | test_channel_reference_a3_11_sources_scope_and_conservation[baseline/current] | 各窗订单/退款订单、完整复合键、目录/支付/退款来源、时间资格、东南排除、互斥穷尽、ΣN/U守恒；实际结果不同于冻结的两类单侧过滤诊断 |

以下值由上述真实计算断言与先行expected逐行比较一致，不是向expected回填的新答案：

| 窗口/组 | N | U | 精确rate |
| --- | --- | --- | --- |
| 基期/channel_app | 1 | 1 | Fraction(1) |
| 基期/channel_web | 2 | 0 | Fraction(0) |
| 基期/总计 | 3 | 1 | Fraction(1,3) |
| 当前/channel_app | 3 | 2 | Fraction(2,3) |
| 当前/channel_web | 1 | 1 | Fraction(1) |
| 当前/总计 | 4 | 3 | Fraction(3,4) |

总体绝对变化Fraction(5,12)，相对变化Fraction(5,4)。每窗按实际组台账查回原始支付与退款来源；四个东南订单及两笔退款不进入固定西北Scope。支付/退款集合均互斥穷尽，分组N/U之和等于实际总计、先行总计及总体参考计数，避免只看U≤N或比率碰巧相等。

函数作用域fixture每次重新读文件、先绑定指纹，yield结束时（包括断言失败时）核对深拷贝与磁盘字节。包装input禁止getitem/get/contains访问expected。退款来源核对使用A3-11每个已退款订单只有一笔事件的固定事实，不编写第二套通用Oracle，不将该假设扩展到未来多退款控制。

## 实际执行证据

环境：开发工作树，CPython 3.10.12、pytest 9.1.1。不是公开工作树或CI；原Provider测试保留在开发全量中，不推算公开通过数量。

### 实施前失败

先新增测试、尚无渠道模块时实际运行：

```bash
.venv/bin/python -B -m pytest tests/test_reference_channel_cohort.py -o addopts='' -q -p no:cacheprovider
```

关键原始输出（省略本机绝对路径）：

```text
ERROR collecting tests/test_reference_channel_cohort.py
E   ModuleNotFoundError: No module named 'reference.channel_cohort'
1 error in 0.12s
```

退出码2，这是新模块尚不存在导致的收集失败，不是业务数值红灯或不符合冻结Oracle的证据。随后只补参考模块，未修订测试预期或冻结数据。

### 新增专项

再次运行同一专项命令，实际退出码0：

```text
...                                                                      [100%]
3 passed in 0.05s
```

### 相关参考与静态测试

```bash
.venv/bin/python -B -m pytest tests/test_reference_channel_cohort.py tests/test_reference_cohort.py tests/test_reference_category_cohort.py tests/test_boundary_fixtures.py -o addopts='' -q -p no:cacheprovider
```

```text
.......................................................................  [100%]
71 passed in 0.31s
```

退出码0；含本轮渠道3项、原总体9项、类别38项及静态21项。总体/类别测试没有修改，原有回归无失败。

### 开发工作树全量

```bash
.venv/bin/python -B -m pytest -o addopts='' -q -p no:cacheprovider
```

因先前已确认沙箱内API/TestClient会停滞，本轮获准直接在沙箱外本地执行，实际退出码0：

```text
........................................................................ [ 52%]
................................................................         [100%]
136 passed in 0.51s
```

本轮没有新的沙箱内全量尝试，不能把历史中断记为本轮事件。136是实际开发全量结果，不是CI、公开分支结果或生产调查系统验收。

## 冻结及实现指纹

| 对象 | SHA-256 |
| --- | --- |
| 11号Fixture完整文件 | d652f050a45279f86b5900b76fdb1327ad9cefdaa114ad61a5d8e6457038f6f8 |
| 独立expected完整JSON | c0e82fc22fb028235f249d524e516920b733636f7ad22ecbb53d7a7b6e811a7e |
| 规范化input | 459879d55d0ebbd0ed4103a628d1946d5e9c58f2aff7e8bbdbcf9804a4f85257 |
| 规范化expected | 27479fab57016e1162c47d90fd7bbae465f8ac4d46ce77e061949db82b8a9b91 |
| 新增reference/channel_cohort.py | 207071252972bbd3cf6de22bc463fbd0c444068966cbb9cfd176b37f2d61629c |
| 新增tests/test_reference_channel_cohort.py | eb33e3775827d1bae1e822a15443df0c30aa6499b863d95d477b149e07ebe804 |

规范化沿用UTF-8编码json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))，不含末尾换行。前四项是既有常量，不随本轮actual更新；测试只将先行字符串转为Fraction，不使用float近似或写回预期。

## 剩余覆盖与交付边界

- 本轮仅完成C01/C02。C03全地区受控对照、C04目录/关键关联故障、C05不足门槛、C06退款控制、C07重排/重复调用等控制仍待后续实际回归，C08展示名补强仍为Should；不将函数里已有防护分支说成这些控制已验收。
- C02中的单侧过滤反例差异、精确计数及来源断言能够识别该固定例的分子/分母Scope错误，但不是执行了一套错误计算器；未运行C03的全地区控制输入。
- 当前未知渠道是最小支持范围拒绝，非完整非关键未知维度处置。未实现region分组、合法双Scope同名正例、贡献分解、生产DQ/授权/SQL/正式序列化，不据固定正例通过宣告G0完成或用户本人验收。
- 只新增参考模块、渠道测试和本记录，并更新reference入口、当前架构及ORACLE的阶段引用。原始/冻结Fixture、独立台账、总体/类别函数、旧测试、生产包及Provider均不改，不更新路线图复选框。
- 本轮未提交或推送；旧方案、冻结记录、起点记录和此前发布证据按其历史时点保留，当前实际状态以本记录为准。

## 最小回归复跑与证据归档（2026-11-03）

这是实现完成后的另一批实际运行，按本次请求重新执行渠道专项及已有总体/类别参考测试；上文实施前收集失败、3/71/136项结果均保留原时点，不改写成此次结果。本节为本次最小回归记录，后续控制覆盖仍待补，不作为用户L3验收记录。

环境：当前仓库开发工作树，CPython 3.10.12、pytest 9.1.1、Linux x86_64，使用已有.venv/bin/python，本地沙箱内执行。环境信息通过解释器实际读取；没有安装依赖或切换/同步分支。

| 本次范围 | 实际命令 | 退出码 | 原始结果 |
| --- | --- | --- | --- |
| 渠道专项 | .venv/bin/python -B -m pytest tests/test_reference_channel_cohort.py -o addopts='' -q -p no:cacheprovider | 0 | 3 passed in 0.05s |
| 渠道、总体、类别组合 | .venv/bin/python -B -m pytest tests/test_reference_channel_cohort.py tests/test_reference_cohort.py tests/test_reference_category_cohort.py -o addopts='' -q -p no:cacheprovider | 0 | 50 passed in 0.21s |

[本次工具原始输出](A3-11_minimal_pytest.txt)保存精确命令、环境、退出码和完整pytest输出，文件SHA-256为`9991c709020a5cee559e84df950bb315e7b86f5b416da69f1e4a9b35cceb9683`。组合50项=渠道3项+总体9项+类别38项，已经包含专项3项，不累计为53项。此次没有运行静态Fixture文件，因而不能把组合50与先前含静态检查的71项差异当成测试丢失。

本次无失败、收集错误或环境阻塞，新增固定回归及所执行的既有参考测试均无失败；不需要为失败作实现/契约归因，也没有修复或调整业务规则。此前缺模块导致的收集失败是实施阶段历史，不属于本次失败。若后续出现数值问题，仍应先定位实现还是契约理解错误，冻结答案不随actual回填。

运行前后核对冻结Fixture及独立expected的磁盘字节和四项既有指纹，均不变；本次只新增输出快照并追加本节，不修改测试、参考/生产代码、冻结数据、旧证据、架构或路线图。C03～C07及C08的待办状态不变。

本次未运行全量pytest、公开工作树pytest或CI，未判断真实权限、生产DQ或用户本人独立能力。**本地pytest通过不等于CI通过、用户L3或用户本人验收通过**，也不据此宣告G0完成；未提交或推送。
