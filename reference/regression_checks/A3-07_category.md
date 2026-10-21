# A3-07 最小类别分组参考计算回归记录


## 公开提交前全量回归（2026-10-21）

在已脱敏的公开工作树复用既有Python测试环境，以如下参数优先导入公开源码（解释器绝对路径不写入公开记录）：

```bash
python -B -m pytest -o pythonpath=src -o addopts='' -q -p no:cacheprovider
```

实际输出：

```text
........................................................................ [ 66%]
....................................                                     [100%]
108 passed in 0.34s
```

公开工作树全量108项通过，比开发工作树113项少5项，差额是未公开的Provider测试；分组回归没有缺失或跳过。公开提交仅同步类别分组参考实现、分组测试、本记录、参考目录说明、Oracle覆盖进展及架构相关段落，不包含未提交Provider、内部归档、环境同步日志或旧开发Git历史。七份Fixture、旧总体参考函数及原测试均保持原样，已在同步前后核对SHA-256；`git diff --check` 通过。公开架构保留自身范围声明，不复制开发目录的Provider说明。

日期：2026-10-21。本记录追加计算覆盖，不重写2026-10-20的静态检查和人工推导历史，不代表用户已完成独立人工验收。

## 实现与独立性边界

新增 [category_cohort.py](../category_cohort.py) 的 `calculate_category_reference(input)`，位于生产包之外，只使用标准库、`Fraction` 以及既有 `calculate_reference()`。新函数不读取文件或 `expected`，不导入生产业务代码，不调用生产SQL或待测分组实现。

总体参考函数仍负责原有支付有效性、半开窗口、单地区Scope、逐单成熟、水位、空队列和订单/退款输入异常；源码与原测试均未改变。新函数共享这些前提，不声称两者是完全独立的总体算法。从原始退款实际重建观察期内的成功退款订单集合，从原始订单经 `(domain_id,snapshot_id,product_id)` 唯一关联产品，按 `category_id` 而非展示名归组。退款按 `(domain_id,snapshot_id,order_id)` 关联并按订单去重。

`categories` 仅是本地展示名目录，按类别复合键解析label；同名不同ID保留两组。缺失产品或类别ID保留在 `__unknown__`；已知类别ID缺展示名仍保留ID、label=None。局部目录出现重复主键或不属于固定域/快照时抛出 `ValueError`，不冒充正式DQ状态。输入字段结构须已核验，不在此新增完整导入Schema。

返回值保留总体结果，另有 `aggregate_rows`、`group_order_ids` 和 `group_refunded_order_ids`。聚合行沿用七个 `AggregateRow` 字段，但率是内存中的精确 `Fraction`，尚不是正式序列化载荷。总计的三个身份字段均为None；分组只输出本窗确有候选订单的类别，不为缺席类别补造零率行。前提不足时两窗均不发布聚合行，仅保留总体候选订单诊断和空业务指标。

## 实际结果与先行冻结预期

输入来自 [07_same_label_distinct_category_ids.json](../../tests/fixtures/order_boundaries/07_same_label_distinct_category_ids.json) 的 `input`；对照依据是 [ORACLE.md](../../tests/fixtures/order_boundaries/ORACLE.md) 中先行逐单推导和JSON的冻结 `aggregate_rows`。下表六行实际结果与既有预期完全一致，未修改预期迎合输出。

| 窗口 | dimension_id / group_id | 展示名 | 实际N | 实际U | 实际率 |
| --- | --- | --- | --- | --- | --- |
| 基期 | null / null | null | 2 | 1 | Fraction(1,2) |
| 基期 | category / category_a | 图书 | 1 | 0 | Fraction(0) |
| 基期 | category / category_b | 图书 | 1 | 1 | Fraction(1) |
| 当前 | null / null | null | 4 | 1 | Fraction(1,4) |
| 当前 | category / category_a | 图书 | 2 | 1 | Fraction(1,2) |
| 当前 | category / category_b | 图书 | 2 | 0 | Fraction(0) |

基期实际支付台账：category_a={S-A-B1}，category_b={S-B-B1}；退款订单台账分别为空和{S-B-B1}。当前支付台账：category_a={S-A-C1,S-A-C2}，category_b={S-B-C1,S-B-C2}；退款订单台账分别为{S-A-C1}和空。订单ID可还原到原输入的source_row_id，并与冻结的分组来源台账逐组比较。每窗支付集合互斥穷尽，退款集合也不跨组：基期N=1+1=2、U=0+1=1；当前N=2+2=4、U=1+0=1。总计率按汇总U/N计算，而非加总分组率。

## 测试覆盖

[test_reference_category_cohort.py](../../tests/test_reference_category_cohort.py) 新增23项测试，分为：六行冻结结果及来源/汇总一致；拒绝访问expected且输入行重排不改变分组；产品关联交换与展示名改名；退款下界、H上界的UTC偏移等价、晚1微秒和失败状态；同单不同事件去重；先地区过滤再分组；未知保留和展示目录缺失；两类目录重复键及域/快照混入；未成熟、支付水位不足、退款水位不足及空基期阻断。

主回归深拷贝整个Fixture，核对调用不修改输入；仅在测试端把已冻结的率字符串转为 `Fraction` 作比较。计算入口实际接收 `input`，额外控制映射在访问 `expected` 时直接报错，证明该路径不依赖静态答案。所有继承的总体结果字段与既有函数对照；旧总体函数不新增分组字段。

## 运行命令与结果

在开发工作树根目录执行：

```bash
.venv/bin/python -B -m pytest tests/test_reference_category_cohort.py -o addopts='' -q -p no:cacheprovider
# 23 passed

.venv/bin/python -B -m pytest tests/test_reference_category_cohort.py tests/test_reference_cohort.py tests/test_boundary_fixtures.py -o addopts='' -q -p no:cacheprovider
# 44 passed

.venv/bin/python -B -m pytest -o addopts='' -q -p no:cacheprovider
# 109 passed
```

44项包含23项新分组回归、9项旧总体参考回归和12项静态Fixture检查。全量109项属于包含本地Provider测试的开发工作树，不冒充公开分支测试数；全量在获准的沙箱外执行，避免已有TestClient沙箱停滞问题。`git diff --check` 通过。

## 冻结与语义保护

新增实现前后核对SHA-256，七份Fixture JSON、旧总体参考函数及测试、静态Fixture测试、Provider及其测试均未修改。其中：

| 文件 | SHA-256 |
| --- | --- |
| A3-07 JSON | e03a1c005e6f99f5e497e452bb3de5e75aa2096f83106f730a45ebcbbec737ac |
| reference/cohort.py | 13b5ced6824c1b8548eaa55b8014f4f87c35562fbe24eead2f0408afbefa96c6 |
| tests/test_reference_cohort.py | f0f7257f9471b4cff6a195332b54d37fc9833682ebd3ac5048739e4dc17c3fe0 |

`ORACLE.md` 只追加本轮覆盖进展和记录链接，旧静态预期与历史运行记录保留。不更新路线图完成复选框，不宣称已有真实数据库、生产分组能力或调查系统验收。

## 尚未覆盖的验收

尚无真实PG/SQL分组、授权与批准导入、正式Decimal50序列化、贡献分解或类别新增/退出的完整冻结样例。地区过滤和未知保留仅有本轮小型控制变体，不替代三维全量场景或正式盲测。`ValueError` 仍是参考输入拒绝，不等于正式 `blocked_by_quality` 结果映射；未来生产实现不得直接导入本函数充当其业务实现。

## 同名与改名回归补强（2026-10-21）

本轮只补强测试和追加实际运行记录，不修改任务2的计算实现或冻结预期。复用已有六行冻结比较，并显式断言四条类别行、两条总计行，率均为精确 `Fraction`。上文23项/44项/109项保留为实现阶段的历史结果。

新增两项按窗口参数化的同名检查，先核对原始输出行列表中确有两个category组，再核对同为“图书”但身份分别为 `(category,category_a)` 和 `(category,category_b)`，不让字典覆盖掩盖重复或丢组。既有改名测试扩为三项：单类别改名、两类别分别改名、两类别改为同名。测试先计算原始输入，再仅修改输入副本中的展示名，逐行比较六条结果；除了相应类别的 `group_label` 外，窗口、分组身份、N/U、率、两条总计及所有其他返回字段必须完全一致，包含两种订单归组台账和总体变化。原Fixture和改名输入均核对未被计算函数修改。

本轮分组测试从23项增至27项，净增4项；相关回归共48项，开发工作树全量113项。没有删除、跳过或放宽原有断言。以下是实际pytest输出，使用 `--no-header` 不输出本机解释器与工作目录绝对路径；未改写测试名、PASSED状态、进度或耗时。

### 分组回归实际输出

```bash
.venv/bin/python -B -m pytest tests/test_reference_category_cohort.py -o addopts='' --no-header -v --tb=short -p no:cacheprovider
```

```text
============================= test session starts ==============================
collecting ... collected 27 items

tests/test_reference_category_cohort.py::test_category_reference_matches_six_frozen_rows_and_manual_sources PASSED [  3%]
tests/test_reference_category_cohort.py::test_category_reference_ignores_expected_and_input_order PASSED [  7%]
tests/test_reference_category_cohort.py::test_product_association_not_display_name_controls_groups PASSED [ 11%]
tests/test_reference_category_cohort.py::test_same_display_label_still_returns_two_distinct_category_groups[baseline] PASSED [ 14%]
tests/test_reference_category_cohort.py::test_same_display_label_still_returns_two_distinct_category_groups[current] PASSED [ 18%]
tests/test_reference_category_cohort.py::test_label_rename_does_not_change_identity_or_counts[rename-one] PASSED [ 22%]
tests/test_reference_category_cohort.py::test_label_rename_does_not_change_identity_or_counts[rename-both-distinct] PASSED [ 25%]
tests/test_reference_category_cohort.py::test_label_rename_does_not_change_identity_or_counts[rename-both-same] PASSED [ 29%]
tests/test_reference_category_cohort.py::test_group_refunds_use_original_closed_observation_period[paid-inclusive] PASSED [ 33%]
tests/test_reference_category_cohort.py::test_group_refunds_use_original_closed_observation_period[horizon-inclusive-offset] PASSED [ 37%]
tests/test_reference_category_cohort.py::test_group_refunds_use_original_closed_observation_period[horizon-one-microsecond-late] PASSED [ 40%]
tests/test_reference_category_cohort.py::test_group_refunds_use_original_closed_observation_period[failed] PASSED [ 44%]
tests/test_reference_category_cohort.py::test_multiple_refund_events_still_count_one_group_order PASSED [ 48%]
tests/test_reference_category_cohort.py::test_single_region_filters_denominator_and_refunds_before_grouping PASSED [ 51%]
tests/test_reference_category_cohort.py::test_unknown_category_preserves_orders_instead_of_dropping_them[product] PASSED [ 55%]
tests/test_reference_category_cohort.py::test_unknown_category_preserves_orders_instead_of_dropping_them[category_id] PASSED [ 59%]
tests/test_reference_category_cohort.py::test_missing_display_catalog_preserves_known_category_id PASSED [ 62%]
tests/test_reference_category_cohort.py::test_duplicate_catalog_key_is_not_silently_overwritten[products] PASSED [ 66%]
tests/test_reference_category_cohort.py::test_duplicate_catalog_key_is_not_silently_overwritten[categories] PASSED [ 70%]
tests/test_reference_category_cohort.py::test_catalog_id_without_matching_domain_and_snapshot_cannot_join[domain_id-products] PASSED [ 74%]
tests/test_reference_category_cohort.py::test_catalog_id_without_matching_domain_and_snapshot_cannot_join[domain_id-categories] PASSED [ 77%]
tests/test_reference_category_cohort.py::test_catalog_id_without_matching_domain_and_snapshot_cannot_join[snapshot_id-products] PASSED [ 81%]
tests/test_reference_category_cohort.py::test_catalog_id_without_matching_domain_and_snapshot_cannot_join[snapshot_id-categories] PASSED [ 85%]
tests/test_reference_category_cohort.py::test_group_publication_inherits_overall_blocking_semantics[immature] PASSED [ 88%]
tests/test_reference_category_cohort.py::test_group_publication_inherits_overall_blocking_semantics[payments] PASSED [ 92%]
tests/test_reference_category_cohort.py::test_group_publication_inherits_overall_blocking_semantics[refunds] PASSED [ 96%]
tests/test_reference_category_cohort.py::test_group_publication_inherits_overall_blocking_semantics[empty_baseline] PASSED [100%]

============================== 27 passed in 0.05s ==============================
```

### 相关回归与全量回归实际输出

```bash
.venv/bin/python -B -m pytest tests/test_reference_category_cohort.py tests/test_reference_cohort.py tests/test_boundary_fixtures.py -o addopts='' -q -p no:cacheprovider
```

```text
................................................                         [100%]
48 passed in 0.13s
```

```bash
.venv/bin/python -B -m pytest -o addopts='' -q -p no:cacheprovider
```

```text
........................................................................ [ 63%]
.........................................                                [100%]
113 passed in 0.36s
```

全量在获准的沙箱外执行，113项属于含未公开Provider测试的开发工作树，不作为公开分支测试数。执行前后核对SHA-256：七份Fixture JSON、`reference/category_cohort.py`、`reference/cohort.py`、原总体与静态测试、Provider及其测试均未改变；本轮仅修改 `tests/test_reference_category_cohort.py` 并追加本记录。关键冻结值如下：

| 文件 | SHA-256 |
| --- | --- |
| reference/category_cohort.py | 9d1d11414f25bcfb61cb79b16e2a4c75d067c54e032c7a5fdd1e95b5456e78ba |
| A3-07 JSON | e03a1c005e6f99f5e497e452bb3de5e75aa2096f83106f730a45ebcbbec737ac |

`git diff --check` 通过。未修改生产包、参考函数接口、冻结预期、路线图或历史运行结果；该回归不代表生产SQL、授权、批准导入、正式序列化或贡献分解已验收。
