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

## C03：全地区合成对照完成（2026-11-05）

新增test_channel_reference_a3_11_all_regions_matches_frozen_counterexample，补齐方案C03。上文C03未完成及旧测试指纹保留原阶段，本节说明当前新增覆盖；不改旧执行结果或先行反例。

### 控制构造与独立预期

从冻结input深拷贝，只将filters.region_ids设为[]，作为假定已另获授权的全地区合成对照；domain_id/snapshot_id、双窗、H、as_of、水位及原始事实/目录均沿用。该假定不实现真实鉴权，也不允许静默改变原西北任务Scope。各次调用均只传input，不读取expected求值。

测试按“西北计算→全地区深拷贝计算→原西北再次计算”顺序执行，后两次均检查输入未变。西北两次完整结果相等，六条聚合行与原expected.aggregate_rows逐项一致；全地区输出只与2026-11-02先行冻结unfiltered_counterexample比较，不新增或回填数值预期。

实际两窗分组与静态反例一致，均使用Fraction：

| Scope/窗口 | channel_web N/U/率 | channel_app N/U/率 | 总计N/U/率 |
| --- | --- | --- | --- |
| 西北/基期 | 2 / 0 / 0 | 1 / 1 / 1 | 3 / 1 / 1/3 |
| 西北/当前 | 1 / 1 / 1 | 3 / 2 / 2/3 | 4 / 3 / 3/4 |
| 全地区/基期 | 3 / 1 / 1/3 | 2 / 1 / 1/2 | 5 / 2 / 2/5 |
| 全地区/当前 | 2 / 1 / 1/2 | 4 / 3 / 3/4 | 6 / 4 / 2/3 |

西北绝对变化5/12、相对变化5/4；全地区绝对变化4/15、相对变化2/3。测试逐项断言两个Scope的每窗指标、六行及两类变化不同，因此误把全地区输出用于西北固定验收会被识别；不编造一套错误业务算法来代替真实控制计算。

### 新增东南来源及守恒

原始订单/退款按(domain_id,snapshot_id,ID)索引。各渠道的全地区支付/退款订单集合，须恰好等于冻结西北集合与先行反例新增集合的并集；差集也必须恰好等于对应渠道的新增集合，禁止额外混入、漏入或串组。

| 窗口/渠道 | 新增支付订单 / source_row_id | 新增退款事件 / source_row_id |
| --- | --- | --- |
| 基期/web | K11-S-B-W1 / r11-order-s-b-web-1 | KR11-S-B-W1 / r11-refund-s-b-web-1 |
| 基期/app | K11-S-B-A1 / r11-order-s-b-app-1 | 无 |
| 当前/web | K11-S-C-W1 / r11-order-s-c-web-1 | 无 |
| 当前/app | K11-S-C-A1 / r11-order-s-c-app-1 | KR11-S-C-A1 / r11-refund-s-c-app-1 |

直接从actual组订单台账查回原始支付和退款，核对渠道、东南地区、有效性、半开支付窗、success、闭合观察期与as_of，以及冻结的additional_order/refund来源集合。固定A3-11每个已退款订单恰有一个原始事件，测试只据该事实做来源追溯，不另写通用退款Oracle。

两种Scope分别检查：每组U集合为N集合子集，组列表无重复、组间互斥，支付并集等于候选队列；ΣN/ΣU等于实际总计、总体参考指标及先行预期。西北基期ΣN=2+1=3、ΣU=0+1=1，当前ΣN=1+3=4、ΣU=1+2=3；全地区基期ΣN=3+2=5、ΣU=1+1=2，当前ΣN=2+4=6、ΣU=1+3=4。无退款的新增东南订单只增加N，不错误增加U。

### 本轮实际执行与指纹

环境：开发工作树、CPython 3.10.12、pytest 9.1.1、Linux x86_64，使用现有.venv/bin/python，本地沙箱内执行。最终命令与结果：

| 范围 | 实际命令 | 退出码 | 输出 |
| --- | --- | --- | --- |
| 渠道C01～C03 | .venv/bin/python -B -m pytest tests/test_reference_channel_cohort.py -o addopts='' -q -p no:cacheprovider | 0 | 4 passed in 0.08s |
| 相关参考与静态 | .venv/bin/python -B -m pytest tests/test_reference_channel_cohort.py tests/test_reference_cohort.py tests/test_reference_category_cohort.py tests/test_boundary_fixtures.py -o addopts='' -q -p no:cacheprovider | 0 | 72 passed in 0.35s |

原始输出保存在[A3-11_C03_pytest.txt](A3-11_C03_pytest.txt)，SHA-256为3ea59f73a6ca8520225a699463b28151a9c2467563ee62c233bd31e507995e91。渠道4项=原C01/C02三项+C03一项；相关72项=渠道4+总体9+类别38+静态21，两组结果是包含关系，不相加。本轮无失败，无需修改业务实现或契约；未运行全量或公开工作树测试，不把此前136/131项历史输出冒称本轮证据。

新增C03后的tests/test_reference_channel_cohort.py指纹为b32c3aaaabbc27746a92320701e55704a88a2424d6c6726f8c8210a904873791。渠道实现仍为207071252972bbd3cf6de22bc463fbd0c444068966cbb9cfd176b37f2d61629c；11号Fixture、独立expected、规范化input/expected分别保持d652f050a45279f86b5900b76fdb1327ad9cefdaa114ad61a5d8e6457038f6f8、c0e82fc22fb028235f249d524e516920b733636f7ad22ecbb53d7a7b6e811a7e、459879d55d0ebbd0ed4103a628d1946d5e9c58f2aff7e8bbdbcf9804a4f85257、27479fab57016e1162c47d90fd7bbae465f8ac4d46ce77e061949db82b8a9b91不变。

C03已完成，C04～C07及C08仍待后续。此次仅扩展测试及其说明和证据，生产/参考实现、冻结输入与答案、旧输出文件和路线图保持不变；本地pytest不是CI、用户L3、真实授权或G0放行。未提交或推送。

## C04：关键关联拒绝控制完成（2026-11-05）

本轮只在既有tests/test_reference_channel_cohort.py新增缺失的断言，使用合法A3-11 input的深拷贝；既有channel_cohort.py已有对应检查，未改渠道/总体/类别函数或既有类别测试。原冻结Fixture、独立expected及先行反例保持原字节。

### 新增覆盖与拒绝证据

| 测试 | 组合/数量 | 核验内容 |
| --- | --- | --- |
| test_channel_reference_c04_rejects_duplicate_catalog_keys | products/regions/channels，3项 | 保留原目录并追加完整业务键相同的行；新增来源行ID保持独立，避免把来源重复混成另一故障。抛ValueError，异常包含“重复目录主键”和对应完整三元键 |
| test_channel_reference_c04_rejects_foreign_catalog_scope | 三种目录×domain_id/snapshot_id，6项 | 保留本地合法行，混入局部ID相同但域或快照不同的目录行；抛含“目录域或快照”及对应ID字段名的ValueError，不能按裸ID静默覆盖或联接 |
| test_channel_reference_c04_rejects_missing_product_before_comparison_gate | 西北/东南目标×ready/immature，4项 | 只将目标订单product_id改成缺失ID；其他订单仍关联合法产品。完整异常文本须含关键关联错误、目标order_id、source_row_id、完整product_key |
| test_channel_reference_c04_preserves_legal_unknown_category | 1项合法兼容 | 产品实体及复合键存在，仅category_id=None；结果ready，六行仍等于冻结渠道预期，完整渠道结果与合法基线相同，不误报关键产品缺失 |

新增共14项：13项预期拒绝、1项合法未知兼容。每个测试还核对传入深拷贝未被计算器修改，沿用函数作用域fixture对原冻结文件及内存对象的前后保护。

缺失产品控制没有删除所有订单共用的product_book实体，以免函数只拒绝首个西北订单、却未实际验证过滤外订单。目标和由通过的异常文本断言确认的字段为：

| 目标 | source_row_id | 缺失完整产品键 | 门槛组合 |
| --- | --- | --- | --- |
| K11-N-C-A3（西北） | r11-order-n-c-app-3 | (domain_a,fixture_single_region_channel_v1_draft,product_missing_c04) | ready、immature均拒绝 |
| K11-S-C-A1（东南） | r11-order-s-c-app-1 | (domain_a,fixture_single_region_channel_v1_draft,product_missing_c04) | ready、immature均拒绝 |

测试在pytest.raises捕获ValueError后，分别断言order_id=目标ID、source_row_id=来源行，以及product_key=完整tuple的repr都出现在异常文本中；不是只断言异常类型。以上为通过的异常断言证据，pytest预期捕获异常不会把它作为用例失败打印。

每个缺失产品用例先调用总体参考函数确认其余前提：ready时reasons为空；immature时只因观察未成熟而insufficient_evidence，支付/退款水位仍为True。测试明确断言西北目标在候选队列、东南目标不在候选队列。随后渠道函数仍抛关键产品异常，证明关联校验覆盖全部原始订单并先于不足返回，不让地区过滤或未成熟掩盖错误。

### 合法未知的兼容边界

本轮合法未知正例是**产品实体存在，仅非关键category_id=None**，不是产品联接失败。原A3-09固定未知、类别未知变体及已知ID缺展示目录等原有类别检查随相关测试一起实际通过，既有类别Oracle和其测试未改。

没有将未知channel_id的参考范围拒绝升级为业务关键DQ；当前最小渠道支持范围仍按已发布方案约束。此处不宣称完整未知渠道保留或所有非关键维度场景已实现。ValueError拒绝也不等于生产blocked_by_quality、DQ Adapter或恢复流程已实现。

### 实际命令、输出与指纹

环境：开发工作树、CPython 3.10.12、pytest 9.1.1、Linux x86_64，使用现有.venv/bin/python，本地沙箱内执行。没有依赖安装、实现修复或预期修改。

| 范围 | 实际命令 | 退出码 | 原始结果 |
| --- | --- | --- | --- |
| C04定向 | .venv/bin/python -B -m pytest tests/test_reference_channel_cohort.py -k c04 -o addopts='' -q -p no:cacheprovider | 0 | 14 passed, 4 deselected in 0.12s |
| 渠道C01～C04 | .venv/bin/python -B -m pytest tests/test_reference_channel_cohort.py -o addopts='' -q -p no:cacheprovider | 0 | 18 passed in 0.13s |
| 相关参考与静态 | .venv/bin/python -B -m pytest tests/test_reference_channel_cohort.py tests/test_reference_cohort.py tests/test_reference_category_cohort.py tests/test_boundary_fixtures.py -o addopts='' -q -p no:cacheprovider | 0 | 86 passed in 0.42s |

最终套件工具输出保存在[A3-11_C04_pytest.txt](A3-11_C04_pytest.txt)，SHA-256为8322ab5b1aee862a98b451d2ea42d14298323d458c8355f7891b91ad4d9736f3。渠道18项=原C01～C03四项+C04十四项；相关86项=渠道18+总体9+类别38+静态21，各范围有包含关系，不相加。无失败，无需为测试失败作实现或契约归因；原来未测试的已有拒绝分支此次直接通过，没有制造或宣称业务红灯。

当前渠道测试文件SHA-256为a06bce2247b8fafba8f669744185d4435dfa1c86478d7aae0c659ea3c7753fe2。渠道实现仍为207071252972bbd3cf6de22bc463fbd0c444068966cbb9cfd176b37f2d61629c，类别实现仍为53507d6ba6671e7ca7ca6cd4f955fa345b53be73bf98edf5fd638d5206f2b216，既有类别测试仍为f5be1f6e7740ed43f26231eaa62d51f75b59d4e16baf2e26821b71becd0387a5。

四项冻结指纹继续绑定d652f050a45279f86b5900b76fdb1327ad9cefdaa114ad61a5d8e6457038f6f8（Fixture）、c0e82fc22fb028235f249d524e516920b733636f7ad22ecbb53d7a7b6e811a7e（独立expected）、459879d55d0ebbd0ed4103a628d1946d5e9c58f2aff7e8bbdbcf9804a4f85257（规范化input）及27479fab57016e1162c47d90fd7bbae465f8ac4d46ce77e061949db82b8a9b91（规范化expected），不从运行结果更新基线。

C04已完成，C05～C07及C08仍待后续。此次未运行全量pytest、公开工作树测试或CI，不将本地通过记为用户L3、用户本人验收或G0放行；未提交或推送。旧证据及其中阶段性待办保留原时点，本节只追加当前C04结论。

## C03/C04定向及全量回归归档（2026-11-05）

本节对应另一批按请求实际执行的归档检查，保留前面C03/C04开发阶段及旧全量记录，不把旧通过数替换成新结果。此次依次执行新增控制定向、渠道专项、相关参考与静态组合，前三阶段均通过后再执行全量；没有新增代码、测试或修订冻结答案。

### 环境、命令与真实结果

解释器与工具信息实际读取为CPython 3.10.12、pytest 9.1.1、Linux x86_64，使用当前开发工作树现有.venv/bin/python，没有安装依赖或切换分支。前三阶段在沙箱内执行；全量因先前API/TestClient沙箱停滞问题获准在沙箱外本地运行。本轮没有重新尝试沙箱内全量，也没有把历史环境中断作为本轮事件。

| 顺序/范围 | 实际命令 | 退出码 | 实际输出 |
| --- | --- | --- | --- |
| 1 / C03+C04定向 | .venv/bin/python -B -m pytest tests/test_reference_channel_cohort.py -k 'all_regions or c04' -o addopts='' -q -p no:cacheprovider | 0 | 15 passed, 3 deselected in 0.12s |
| 2 / 渠道专项 | .venv/bin/python -B -m pytest tests/test_reference_channel_cohort.py -o addopts='' -q -p no:cacheprovider | 0 | 18 passed in 0.12s |
| 3 / 相关参考与静态 | .venv/bin/python -B -m pytest tests/test_reference_channel_cohort.py tests/test_reference_cohort.py tests/test_reference_category_cohort.py tests/test_boundary_fixtures.py -o addopts='' -q -p no:cacheprovider | 0 | 86 passed in 0.41s |
| 4 / 开发全量 | .venv/bin/python -B -m pytest -o addopts='' -q -p no:cacheprovider | 0 | 151 passed in 0.59s |

完整工具原始合并输出保存于[A3-11_controls_pytest.txt](A3-11_controls_pytest.txt)，SHA-256为`53a7dccf037d53240a39d85fdd8301aa5ac5d8d768a3bb2ead21ec8b626348b2`。文件同时登记每阶段精确命令、退出码、解释器/pytest环境与执行范围，不从历史摘要拼接本次通过结果。

定向15项=C03一项+C04十四项，其中C04包含13项预期拒绝及1项合法未知兼容；渠道18项包含原C01/C02三项，均无回归。相关86项=渠道18+总体9+类别38+静态21，原总体/类别参考测试均通过。各阶段为包含关系，不能累加为总测试量。

全量151项是此次开发工作树实际运行数量，包含当前未公开Provider测试；没有从此前开发136或公开131项加减推算。此次未在公开工作树运行，也未查询或触发CI。**本地pytest通过不代表CI、GitHub Actions、用户本人L3或独立人工验收通过。**

### 失败归因与文件保护

本轮四阶段均无测试失败、收集错误或环境阻塞，无需修改实现或契约。没有通过更新expected消除失败。若后续出现失败，仍须先保存原始输出、核对冻结契约与实现责任，再决定修复位置；禁止依据actual回填冻结预期。

运行前后均核对以下四项冻结指纹并匹配原有常量，Fixture.expected与独立台账.expected仍相等：

| 冻结对象 | SHA-256 |
| --- | --- |
| 11号Fixture完整文件 | d652f050a45279f86b5900b76fdb1327ad9cefdaa114ad61a5d8e6457038f6f8 |
| 独立expected完整JSON | c0e82fc22fb028235f249d524e516920b733636f7ad22ecbb53d7a7b6e811a7e |
| 规范化input | 459879d55d0ebbd0ed4103a628d1946d5e9c58f2aff7e8bbdbcf9804a4f85257 |
| 规范化expected | 27479fab57016e1162c47d90fd7bbae465f8ac4d46ce77e061949db82b8a9b91 |

规范化沿用UTF-8编码的json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))，不含末尾换行。渠道实现仍为207071252972bbd3cf6de22bc463fbd0c444068966cbb9cfd176b37f2d61629c，渠道测试仍为a06bce2247b8fafba8f669744185d4435dfa1c86478d7aae0c659ea3c7753fe2；运行本身未改变源码/断言或原始冻结文件。

本次只新增原始输出快照并追加本节，保留前面记录及旧输出原文；未修改参考/生产函数、类别Oracle、测试、Provider、架构或路线图。C01～C04已有本轮真实证据，C05～C07及C08待办状态不变；不据全量通过宣告G0或生产调查能力完成。未提交或推送。

## C05：成熟、水位、空基期与合法零退款（2026-11-05）

本轮先依DD02 §2、先行逐单记录与冻结实施契约直接填写[C05独立预期JSON](../manual_checks/A3-11_C05_expected.json)及[推导说明](../manual_checks/A3-11_C05_expected.md)，再编写和执行C05测试。没有调用参考/生产函数生成答案；已阅读现有实现，不称首次盲审或用户本人签字。原11号Fixture与A3-11_expected.json不改，新控制只用于深拷贝变体，不计新增主Fixture。

### 单故障控制及预期状态

西北最大成熟时刻为2026-09-19T00:00:00Z，窗口最大end为09-15零点。四种不足控制及其独立预期：

| 控制 | 唯一业务修改 | 应返回原因 | 三个成熟/水位标志 |
| --- | --- | --- | --- |
| immature | as_of=09-18T23:59:59.999999Z | 观察期未成熟 | False/True/True |
| payments_below | payments_through=09-14T23:59:59.999999Z | 支付水位不足 | True/False/True |
| refunds_below | refunds_through=09-18T23:59:59.999999Z | 退款水位不足 | True/True/False |
| empty_baseline | 三笔西北基期支付全部设无效 | 支付窗口无有效样本 | True/True/True |

前三个分别只差1微秒；不足均应返回insufficient_evidence及唯一对应原因，**两窗N/U/rate及两类变化全部None、aggregate_rows=[]、group_order_ids={}、group_refunded_order_ids={}**。不允许只阻断基期而发布当前正常指标，也不把无发布值当0。候选队列保留诊断；空基期必须是[]、当前四单仍保留，东南有效订单不得让基期误变非空。

本组是结构/关联合法但比较前提不足，测试要求上述正常不足状态；不是抛ValueError的关键关联/非法结构场景，不实现生产blocked_by_quality。测试直接对照先行静态blocked_publication；另比较总体函数只确认原语义未改，不能用总体函数现场返回值替代独立预期。

### 等号允许及零退款正例

三个等号控制分别将as_of设为09-19零点、payments_through设为09-15零点、refunds_through设为09-19零点，均应ready并逐项复用原冻结六行、组订单台账及总体变化。支付水位等号本来就是合法输入已有正例，此次明确作为负边界的配对检查，不另创建同内容主Fixture。被排除东南订单09-21才成熟，不影响固定西北的成熟或退款水位判断。

零退款正例只移除KR11-N-B-A1，保持基期三笔支付有效、双窗非空且成熟水位完整；东南基期KR11-S-B-W1仍存在并必须排除。独立预期为：

| 窗口/组 | N | U | 精确rate |
| --- | --- | --- | --- |
| 基期/网页 | 2 | 0 | Fraction(0) |
| 基期/移动应用 | 1 | 0 | Fraction(0) |
| 基期/总计 | 3 | 0 | Fraction(0) |
| 当前/网页 | 1 | 1 | Fraction(1) |
| 当前/移动应用 | 3 | 2 | Fraction(2,3) |
| 当前/总计 | 4 | 3 | Fraction(3,4) |

实际结果与上表先行预期一致，outcome=ready，绝对变化Fraction(3,4)，相对变化None。相对变化为空只因基期率为0，不使整次比较或六行输出被阻断。N=0与N>0/U=0在状态、发布字段和组台账上有明确区别。

### 指纹、执行与剩余边界

C05预期JSON在首次运行前的SHA-256为`cbe71efb6734e3480f5d1ad93793d4338c240377dec5cb3335c01136c7565819`，测试中固定该常量并核对原来源Fixture/expected/input指纹。该预期的内存和磁盘也在每项测试结束后检查不变；三个等号直接引用既有预期，合法零退款的六行与变化均为先行手填值，不根据actual回填。

新增测试为四项参数化不足、三项参数化等号允许、一项零退款，共8项；控制装配仅应用记录的context字段、支付有效性或退款事件移除，输入深拷贝在函数调用前后保持不变。环境为开发工作树、CPython 3.10.12、pytest 9.1.1、Linux x86_64，使用现有.venv/bin/python，沙箱内本地执行：

| 范围 | 实际命令 | 退出码 | 真实结果 |
| --- | --- | --- | --- |
| C05定向 | .venv/bin/python -B -m pytest tests/test_reference_channel_cohort.py -k c05 -o addopts='' -q -p no:cacheprovider | 0 | 8 passed, 18 deselected in 0.12s |
| 渠道C01～C05 | .venv/bin/python -B -m pytest tests/test_reference_channel_cohort.py -o addopts='' -q -p no:cacheprovider | 0 | 26 passed in 0.16s |
| 相关参考与静态 | .venv/bin/python -B -m pytest tests/test_reference_channel_cohort.py tests/test_reference_cohort.py tests/test_reference_category_cohort.py tests/test_boundary_fixtures.py -o addopts='' -q -p no:cacheprovider | 0 | 94 passed in 0.45s |

最终套件的完整工具输出保存在[A3-11_C05_pytest.txt](A3-11_C05_pytest.txt)，SHA-256为`3f5e078ad11e3af515d1aac080292630c3d4793a0342195ae6dcddc6b68c8878`。渠道26项=原18+C05八项；相关94项=渠道26+总体9+类别38+静态21，范围重叠不相加。本轮无失败、无实现修复、无契约或答案回填；新增既有不足分支的测试直接通过，不捏造业务红灯。

当前渠道测试指纹为824a280cf3e573cb6067f1ad215fb41225bfaf4dfc7b063e5eb33a6620905a8d。渠道实现仍为207071252972bbd3cf6de22bc463fbd0c444068966cbb9cfd176b37f2d61629c；原四项冻结指纹继续为d652f050a45279f86b5900b76fdb1327ad9cefdaa114ad61a5d8e6457038f6f8（Fixture）、c0e82fc22fb028235f249d524e516920b733636f7ad22ecbb53d7a7b6e811a7e（独立expected）、459879d55d0ebbd0ed4103a628d1946d5e9c58f2aff7e8bbdbcf9804a4f85257（input）和27479fab57016e1162c47d90fd7bbae465f8ac4d46ce77e061949db82b8a9b91（expected）。

C05已完成，C06/C07及C08仍待后续。生产/总体/类别/渠道实现、原Fixture、原台账及旧执行输出不改；本轮未跑全量或公开工作树pytest，不将历史151等数量当作此次结果。本地pytest不是CI、用户L3或用户本人验收，不据此宣告G0或生产能力完成；未提交或推送。

## C06：按正式定义完成退款去重及观察期控制（2026-11-05）

### 定义核对与已有覆盖

首先读取公开提交c9b8536a6d26287a845a978f0cd59f4b99a79169中的[实施方案](../manual_checks/A3-11_channel_oracle_plan.md)，确认本地原字节一致、SHA-256为178c5061a1741f3f85688fdfc21c197a9fd4be604e1cc1db7031604cc3f3eb08。§6 C06的正式定义仍为“独立退款扫描仍按订单去重及观察期”：同单追加不同refund_id的有效success事件不增加U，追加failed、H后或as_of后事件也不增加U。没有把C05门槛、C07重排或C08展示名等工作改编号到C06。

现有渠道实现已有对应退款扫描和订单集合去重；C01/C02固定例只有每个退款订单一笔事件，C05移除事件也不等同追加事件控制。此前没有渠道C06测试；既有总体/类别退款覆盖不能替代渠道扫描断言，因此本轮只补缺失测试，不修改三种参考算法。

### 输入、先行预期与断言

先按DD02与原始支付/退款手工保存[事件清单与预期](../manual_checks/A3-11_C06_expected.json)、[推导及范围说明](../manual_checks/A3-11_C06_expected.md)，再编写并执行测试。JSON含方案来源/指纹、Scope、每个新增refund_id/source_row_id/订单/时刻/状态及属性依据；测试固定其SHA-256为32ecd37ddf05767c5496362c8f0f3529d8a905412cd6c1b78ae8d8a42c52ae03，并检查输入/原答案来源指纹。未从actual生成预期，非首次盲审或用户签字。

新增test_channel_reference_c06_refund_events_keep_frozen_order_metrics，按四类×双窗参数化共8项。每项只在独立深拷贝上追加一笔事件，不累计八笔；域/快照/地区/H/双窗/as_of/水位及支付不变。追加前检查事件ID与来源唯一、订单实体存在、支付有效、属于指定西北支付窗与渠道、退款不早于支付，不混入其他故障。

| C06原定义内的类型 | 基期控制 | 当前控制 | 验收断言 |
| --- | --- | --- | --- |
| second_success | 已退款K11-N-B-A1追加09-06 success，原09-05已有退款 | 已退款K11-N-C-W1追加09-11 success，原09-10已有退款 | 两笔事件ID/来源不同且均在H内、<=as_of；该单事件数1→2，实际退款订单台账仍只出现该订单一次 |
| failed | 原未退款K11-N-B-W1追加09-03 failed | 原未退款K11-N-C-A3追加09-13 failed | 时间有效且<=as_of，仅状态失败，该单不进入U |
| after_horizon | K11-N-B-W1追加09-09T00:00:00.000001Z success | K11-N-C-A3追加09-19T00:00:00.000001Z success | 恰晚paid_at+H 1微秒且<=as_of，不进入U |
| after_as_of | K11-N-B-W1追加09-23T00:00:00.000001Z success | K11-N-C-A3追加同一时刻success | 恰晚as_of 1微秒，同时在H后，不能进入U；不声称孤立验证as_of |

时间均为2026年UTC。三个负类型选择原未退款订单，若错误计入就会改变U，不会被原订单已退款的去重掩盖。第二笔success控制显式核对原/新事件属于相同完整订单键，且各自时间和状态有效；不沿用C02“每个退款订单只有一事件”的来源假设。

所有8项实际均ready，六条聚合行逐项与原独立冻结expected相等，rate/变化为精确Fraction；候选支付集合、两个组台账、成熟水位标志及总体指标均不变。基期总计3/1/率1/3，当前4/3/率3/4，绝对变化5/12、相对变化5/4，目标渠道U变化0。旧预期直接复用，没有为C06另算或回填六行答案；事件清单和输入副本也检查前后不变。

### 范围限制与实际执行

按原方案限制，成熟已满足时paid_at+H<=as_of，不存在“H内但as_of后”的事件。本轮after_as_of同时在H后，只验证该合法时间组合被忽略，不宣称独立检验as_of条件的必要性；没有为制造孤立场景而提前as_of，避免改变C05成熟门槛。

环境：开发工作树，CPython 3.10.12、pytest 9.1.1、Linux x86_64，使用现有.venv/bin/python，沙箱内本地实际执行：

| 范围 | 实际命令 | 退出码 | 真实结果 |
| --- | --- | --- | --- |
| C06定向 | .venv/bin/python -B -m pytest tests/test_reference_channel_cohort.py -k c06 -o addopts='' -q -p no:cacheprovider | 0 | 8 passed, 26 deselected in 0.15s |
| 渠道C01～C06 | .venv/bin/python -B -m pytest tests/test_reference_channel_cohort.py -o addopts='' -q -p no:cacheprovider | 0 | 34 passed in 0.20s |
| 相关参考与静态 | .venv/bin/python -B -m pytest tests/test_reference_channel_cohort.py tests/test_reference_cohort.py tests/test_reference_category_cohort.py tests/test_boundary_fixtures.py -o addopts='' -q -p no:cacheprovider | 0 | 102 passed in 0.47s |

完整最终套件工具输出保存在[A3-11_C06_pytest.txt](A3-11_C06_pytest.txt)，SHA-256为43e8916e92f5b0b9191ebc4f7c8382efcb036263b0b50f5ee39e1b7f2fcca3ea。渠道34项=原C01～C05二十六项+C06八项；相关102项=渠道34+总体9+类别38+静态21，范围包含不相加。既有C01～C05原断言保持，本轮一起实际通过；无失败，无实现或契约修复，不制造业务红灯。

当前渠道测试SHA-256为5441075b1bfb3da7cff63d1f825b74023b383230b2e26e4e41ee2cc947d667d4。渠道实现仍为207071252972bbd3cf6de22bc463fbd0c444068966cbb9cfd176b37f2d61629c；原Fixture/独立expected/input/expected继续保持d652f050a45279f86b5900b76fdb1327ad9cefdaa114ad61a5d8e6457038f6f8、c0e82fc22fb028235f249d524e516920b733636f7ad22ecbb53d7a7b6e811a7e、459879d55d0ebbd0ed4103a628d1946d5e9c58f2aff7e8bbdbcf9804a4f85257、27479fab57016e1162c47d90fd7bbae465f8ac4d46ce77e061949db82b8a9b91四项指纹。

C06按原定义完成，C07及C08待后续。本轮未运行全量、公开工作树或CI，未改生产/总体/类别/渠道代码、已发布方案、原冻结输入/预期或旧输出；不据本地pytest宣称用户L3、用户本人验收或G0放行。未提交或推送。

## C05定向复跑与C03/C04证据索引归档（2026-11-05）

本节保存本批次新执行的C05及当前渠道专项结果，同时索引C03/C04已有证据。既有原始输出原文件保留，只重新计算哈希确认，没有将旧通过数量写成本轮结果，也没有重新生成预期。

### 本轮实际执行

环境由解释器实际读取：CPython 3.10.12、pytest 9.1.1、Linux x86_64，当前开发工作树，现有.venv/bin/python，沙箱内本地运行。未安装依赖或切换分支。

| 本轮范围 | 实际命令 | 退出码 | 原始结果 |
| --- | --- | --- | --- |
| C05定向 | .venv/bin/python -B -m pytest tests/test_reference_channel_cohort.py -k c05 -o addopts='' -q -p no:cacheprovider | 0 | 8 passed, 26 deselected in 0.13s |
| 当前渠道C01～C06 | .venv/bin/python -B -m pytest tests/test_reference_channel_cohort.py -o addopts='' -q -p no:cacheprovider | 0 | 34 passed in 0.19s |

完整工具合并输出保存在[A3-11_C05_recheck_pytest.txt](A3-11_C05_recheck_pytest.txt)，SHA-256为`b5636e53d8f9cea759118777192f17833cc0e2f77205138600492c854b3295ac`。C05八项属于渠道34项子集，不相加。当前渠道专项包含C03/C04及原C01/C02，均有本批次实际执行；下表旧证据仍是各自阶段的输出。

本轮失败原因：无。未出现断言失败、收集错误或环境阻塞，无需在实现错误与契约误解之间做修复归因；没有改实现、契约或答案来消除失败。此前阶段的缺模块失败和沙箱全量停滞都不是本轮事件。

### C03/C04历史证据索引

下列旧文件实际存在，重新计算SHA-256与原记录匹配；日期均为2026-11-05，但属于不同开发阶段。本次只归档索引，不覆盖或伪造原始输出，不把阶段范围差异当作测试丢失。

| 原证据文件 | 原运行范围/实际数量 | SHA-256 |
| --- | --- | --- |
| [C03输出](A3-11_C03_pytest.txt) | 当时渠道C01～C03：4 passed；相关：72 passed；退出码均0 | 3ea59f73a6ca8520225a699463b28151a9c2467563ee62c233bd31e507995e91 |
| [C04输出](A3-11_C04_pytest.txt) | C04定向：14 passed/4 deselected；当时渠道：18 passed；相关：86 passed；退出码均0 | 8322ab5b1aee862a98b451d2ea42d14298323d458c8355f7891b91ad4d9736f3 |
| [C03/C04定向及全量归档](A3-11_controls_pytest.txt) | 定向15 passed/3 deselected、渠道18 passed、相关86 passed、开发全量151 passed；退出码均0 | 53a7dccf037d53240a39d85fdd8301aa5ac5d8d768a3bb2ead21ec8b626348b2 |
| [C05创建阶段输出](A3-11_C05_pytest.txt) | C05定向8 passed/18 deselected、当时渠道26 passed、相关94 passed；退出码均0 | 3f5e078ad11e3af515d1aac080292630c3d4793a0342195ae6dcddc6b68c8878 |

原命令和完整输出见各文件；C03为全地区对照，C04为关键关联拒绝及合法未知兼容，控制编号不变。当前渠道34项已包含后续C05/C06，因此不把旧渠道4/18/26项当作当前套件数量，也不合计各阶段passed数为样本量。

### 输入、预期与执行版本

运行前后核对原Fixture和独立expected磁盘字节，并核对规范化输入/预期；另核对C05独立控制记录。以下指纹均保持不变：

| 对象 | SHA-256 |
| --- | --- |
| 11号Fixture完整文件 | d652f050a45279f86b5900b76fdb1327ad9cefdaa114ad61a5d8e6457038f6f8 |
| 独立A3-11_expected.json | c0e82fc22fb028235f249d524e516920b733636f7ad22ecbb53d7a7b6e811a7e |
| 规范化input | 459879d55d0ebbd0ed4103a628d1946d5e9c58f2aff7e8bbdbcf9804a4f85257 |
| 规范化expected | 27479fab57016e1162c47d90fd7bbae465f8ac4d46ce77e061949db82b8a9b91 |
| C05控制预期JSON | cbe71efb6734e3480f5d1ad93793d4338c240377dec5cb3335c01136c7565819 |
| 本轮渠道测试文件 | 5441075b1bfb3da7cff63d1f825b74023b383230b2e26e4e41ee2cc947d667d4 |
| 渠道参考函数 | 207071252972bbd3cf6de22bc463fbd0c444068966cbb9cfd176b37f2d61629c |

规范化沿用UTF-8编码json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))，无末尾换行。没有依据actual更新任何基线，C05和原始Fixture的fixture结束保护继续检查内存与磁盘不变。

### 本地测试与CI的边界

**以上新执行和旧归档全部是本地pytest证据，不是GitHub Actions CI，也不是用户本人L3或独立人工验收。** 本轮未运行或查询GitHub Actions，不声称Actions通过。此前公开工作树运行也仍是本地执行，不能因已推送过文件就改称CI。

本轮只运行表中的两条命令，未运行总体/类别组合、静态套件、全量或公开工作树pytest；历史102/151等数量不计本轮结果。只新增本次输出快照并追加此索引，旧证据、代码、测试、冻结数据、架构和路线图保持不变；C07/C08状态不变，不据归档宣告G0通过。未提交或推送。

## C07：重复调用、结果隔离及输入重排（2026-11-06）

### 契约与已有覆盖

按[实施方案§6的C07](../manual_checks/A3-11_channel_oracle_plan.md)补充输入隔离。既有C01已经只传input，使用_InputOnly在getitem/get/contains探测expected时直接报错；共享channel_fixture逐测试重新加载冻结文件，核对四项指纹，finally检查原输入/预期内存及文件字节不变。上述辅助代码及C01～C06原断言逐字节保留，没有重写另一套保护测试。

新增两项控制只验证缺失性质，未新增或修改冻结答案：

1. `test_channel_reference_c07_repeated_calls_and_results_are_isolated`：从冻结input深拷贝并用_InputOnly包装；首次与重复调用值一致。调用者再修改首次结果中的reasons、quality_checks、嵌套metrics、聚合行、候选订单和两类分组台账，第二次结果和输入仍不变。随后在另一份深拷贝上清空地区过滤，调用假定另获授权的全地区合成Scope；确认结果确实有别，再调用原西北输入及其新副本，均等于未污染的原结果，全地区先前结果亦不变。原输入和全地区控制各自前后相等。全地区具体数值继续由C03独立冻结反例验收，不在C07复制数值Oracle。
2. `test_channel_reference_c07_reordering_preserves_groups_and_candidate_sets`：只逆序orders、refunds及dimensions下所有目录列表。六条聚合行按原有身份辅助函数比较，两类分组台账完全相等，outcome/reasons/quality_checks/metrics一致；candidate_order_ids按窗口比较集合，避免把原始候选顺序当成契约。该变体计算前后也不变。

重复调用控制是同一pytest进程内首次、重复、交错Scope及修改返回值的隔离检查，不宣称覆盖独立进程启动、文件读取拦截或所有潜在全局依赖。返回值比较是重排/隔离性质，不是从实际输出生成新业务预期；C01/C02仍承担六行数值及来源的独立冻结验收。

### 实际执行

环境：开发工作树，CPython 3.10.12、pytest 9.1.1、Linux x86_64；解释器为仓库.venv/bin/python。实际命令、退出码和完整输出见[A3-11_C07_pytest.txt](A3-11_C07_pytest.txt)，SHA-256为`40d9ca8f4beb331f212fa02d29ce85726915ff0b53c6e7ed068ca76a63b7f2e4`。

| 范围 | 实际结果 | 退出码 |
| --- | --- | --- |
| 渠道文件，-k c07 | 2 passed, 34 deselected in 0.13s | 0 |
| 渠道专项 | 36 passed in 0.19s | 0 |
| 渠道＋总体＋类别＋静态Fixture | 104 passed in 0.46s | 0 |

36项=原C01～C06三十四项+C07两项；104项=渠道36+总体9+类别38+静态21，范围重叠不相加。新增控制首次定向运行也是2 passed, 34 deselected in 0.13s；随后按表中三条命令执行并保存原始输出，未出现失败、实现修复或契约修订。未运行全量或公开工作树测试，不把历史全量数量计为本轮结果。

### 指纹与状态

渠道测试新SHA-256为`e225f4810520a7071f14ca12b321db6aee0a28c547f510ee17d1b100bf6d04d2`。本轮前后核对：原Fixture完整文件仍为d652f050a45279f86b5900b76fdb1327ad9cefdaa114ad61a5d8e6457038f6f8，独立expected文件仍为c0e82fc22fb028235f249d524e516920b733636f7ad22ecbb53d7a7b6e811a7e；共享fixture另核对规范化input/expected原指纹并检查磁盘不变。渠道实现仍为207071252972bbd3cf6de22bc463fbd0c444068966cbb9cfd176b37f2d61629c，方案仍为178c5061a1741f3f85688fdfc21c197a9fd4be604e1cc1db7031604cc3f3eb08。

C07按方案补齐，C08展示名仍待后续。只新增测试和本地证据并同步入口/架构覆盖说明；总体、类别、渠道实现、主Fixture/expected、Provider及旧证据保持不变，路线图状态不改。本地pytest不是GitHub Actions CI、用户本人L3或人工验收，不据此宣告生产Runtime或G0通过。本轮未提交或推送；公开工作树仍保留前次已推送版本。

## C07补强：各列表分别逆序及重复执行（2026-11-06）

### 缺口与控制预期

前一节只有“全部列表联合逆序”一项，不能单独定位某类列表的顺序依赖。本轮将同一重排测试参数化为orders、refunds、products、categories、channels、regions、all七项；保留前次重复调用/交错Scope/修改旧返回值的隔离测试，不复制C01、_InputOnly或冻结哈希辅助代码，C07共8项。

以下为依据输入和契约预先确定的性质，不生成新业务expected：订单/退款的行序不改变业务键或合格集合；目录按完整复合键关联，目录行序不影响归属；未被引用的合法目录项不影响任何订单的关联或聚合。两窗N/U、Fraction、分组身份和两类分组订单台账均应不变，总体candidate_order_ids只比较集合。C01/C02继续对照先行冻结六行和来源，重排控制不替代独立数值Oracle。

| 参数 | 深拷贝上的控制 | 独立预期依据 |
| --- | --- | --- |
| orders | 仅逆序支付订单 | 支付窗、Scope、成熟及退款订单归属由字段和键决定 |
| refunds | 仅逆序退款事件 | 成功退款按业务订单去重，扫描顺序不改变退款订单集合 |
| products | 追加合法未引用产品，再逆序产品目录 | 订单仍引用原产品完整复合键，未引用产品不应参与分组 |
| categories | 追加合法未引用类别，再逆序类别目录 | 渠道分组不使用类别展示顺序，未引用类别不改变任何归属 |
| channels | 仅逆序渠道目录 | 渠道ID确定身份，目录顺序不参与分组 |
| regions | 仅逆序地区目录 | 过滤使用地区ID，目录顺序不改变授权合成Scope |
| all | 深拷贝补上述两项后联合逆序所有列表 | 单项规则组合后仍应保持聚合与台账不变 |

原产品和类别目录各仅1行，直接逆序没有区分力。因此对应控制中复制原行，保留合法域/快照及其他字段，仅对ID和source_row_id追加`_c07_unused`，并确认未被订单/产品引用；不新增订单或退款。先计算追加后的结果，再逆序；两阶段均与原始结果比较，避免把新增目录项的影响混为顺序影响。每个待逆序列表明确断言至少两行、首尾不同，确保实际产生重排。所有变化仅在内存深拷贝中，未修改固定Fixture或独立expected。

每项依次调用原始输入、追加目录项后的控制、逆序后的控制、同一逆序输入第二次调用、原始输入；对应聚合按既有身份辅助函数比较，两类分组台账完全相等，metrics/outcome/reasons/quality_checks不变，六行及两窗率均显式检查Fraction类型。每次控制计算后检查输入未变，并在恢复原始输入调用后再次检查控制输入。此处只检查候选集合，不对跨变体候选顺序作断言；原C07隔离测试继续检测旧返回值修改和跨Scope污染。

### 实际命令与结果

环境：本地开发工作树，CPython 3.10.12、pytest 9.1.1、Linux x86_64；使用仓库.venv/bin/python。完整命令、退出码及原始输出见[A3-11_C07_reordering_pytest.txt](A3-11_C07_reordering_pytest.txt)，SHA-256为`c4b06e6a3f858f242061aaef4584c65cd5df96cfeb5f3d36f18e7cfa4efcb49c`。

| 范围 | 实际结果 | 退出码 |
| --- | --- | --- |
| 渠道文件，-k c07 | 8 passed, 34 deselected in 0.14s | 0 |
| 渠道专项 | 42 passed in 0.21s | 0 |
| 渠道＋总体＋类别＋静态Fixture | 110 passed in 0.47s | 0 |

42项=原C01～C06三十四项+C07隔离一项+重排七项；110项=渠道42+总体9+类别38+静态21。七项替代原联合逆序一项，净增6项，不把专项子集与相关结果相加。首次定向也是8 passed, 34 deselected in 0.14s；最终修改完成后按表中三条命令重新执行并保存输出，无失败、无实现或契约修复。

### 指纹与边界

新渠道测试SHA-256为`d4fb4abaf6ade2d2fadbf20385943011e02db9b3e015a90b66da452712477817`。原C01～C06、保护辅助及前次C07隔离测试逐字节保留；冻结Fixture、独立expected、实施方案、三种参考计算器、Provider及前次C07原始输出均与本轮开始时指纹一致。四项主冻结指纹仍由既有channel_fixture逐测试核对和finally保护，未使用运行结果覆盖预期，旧证据中的36/104等阶段数量保留原文。

本轮仅扩展C07重排测试、追加新输出与本节，并同步reference入口和架构覆盖数量。未运行全量pytest、公开工作树或GitHub Actions，未提交/推送；本地通过不等于CI、用户本人L3、独立人工验收或生产G0放行。C08仍待后续，路线图状态未更改。

## 完整回归与Must关闭评审（2026-11-06）

本轮没有新增或修改测试、参考计算器、冻结输入或答案。按实施方案依次实际执行：渠道专项42 passed in 0.22s、相关参考及静态110 passed in 0.48s、开发工作树全量175 passed in 0.66s，退出码均为0；范围包含不相加。渠道专项增加-rA，原始输出列出42条真实PASSED身份，C01～C07分别为1/2/1/14/8/8/8项。

完整命令、环境说明及输出见[A3-11_full_regression_pytest.txt](A3-11_full_regression_pytest.txt)，SHA-256为c312638e0264bc73d96ff110f1eae05e9351f883feadb491c38fcf197fcf8d5a；[公开版本摘要](A3-11_full_regression_public_manifest.json)另行绑定公开工作树的实际运行文件及复跑结果；历史完整47文件开发清单保留本地，其规范化映射SHA-256为d6f59929ba6e63c75057e7c30a24662123213a0cac09db46bbd59954a4d08038，不冒充公开摘要的映射哈希。渠道测试仍为d4fb4abaf6ade2d2fadbf20385943011e02db9b3e015a90b66da452712477817，本轮运行前后清单内文件、主冻结四项指纹、C05/C06预期及旧输出全部不变。

逐项范围、限制及关闭决定见[A3-11_Must_review.md](A3-11_Must_review.md)：**仅关闭本地A3-11最小渠道参考C01～C07 Must**。C08 Should、未知渠道/region/合法跨域/贡献等G0缺口、生产实现和用户本人验收不关闭；G0 M01整体仍开放。

本轮全量因既有API/TestClient沙箱内停滞记录获准在沙箱外本地执行，没有新增沙箱内全量失败。所有结果不是GitHub Actions CI；本轮未运行公开工作树、查询远程或提交/推送。公开基线91e215d只含C01～C06，当前C07尚未提交；用实际源码哈希绑定本次证据，不把开发HEAD或公开提交号冒充已包含运行版本。公开交付及最终提交核对仍待后续，不改写旧阶段证据。

## 后续公开交付验证（2026-11-06）

以上保留开发阶段范围与状态；本次已在公开候选工作树实际通过渠道42项、相关110项、全量170项，源码与冻结指纹不变，见[公开交付验证](A3-11_C07_publication.md)。C07及本评审随此次公开追加提交交付；公开版本摘要绑定45份运行文件，完整内部开发清单保留本地。本地公开pytest仍不是CI或本人验收，仅关闭A3-11最小渠道参考Must，G0与C08保持原边界。
