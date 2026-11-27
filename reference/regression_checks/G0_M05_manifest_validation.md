# G0 M05 开发数据清单完整性检查

从仓库根目录运行标准库脚本。退出码 0 表示检查通过，1 表示清单或证据检查失败。可用 `--manifest` 指定临时清单，用 `--root` 指定证据副本根目录。

```bash
python3 -I -B reference/regression_checks/check_g0_development_manifest.py
```

校验文件、JSON 对象、证据单行及源码片段的 SHA-256，并核对预期定位、规则集、审阅记录和日志中的完整测试节点。控制变体按已登记配方重放输入，地区变体的输入指纹与冻结变更记录对照。脚本读取既有的冻结预期。初次验证时本人签收均为 `pending_user_confirmation`。开发清单写入 `approved` 会导致检查失败。

首次检查发现两条测试节点 ID 在参数化描述中的空格处被截断，已按原始执行记录补全。公开候选的用例、冻结预期和审阅状态与开发清单一致，执行索引按公开树实际配置和历史证据重新绑定。[开发数据清单](G0_development_manifest.json) · [本人复核表](../manual_checks/G0_M05_independent_review.md)

## 公开候选本地执行

2026-11-24（Asia/Shanghai），以公开提交 `a479fad` 为源码锚点，使用 CPython 3.10.12、pytest 9.1.1、Linux x86_64。下列命令中的 `python` 为现有测试环境解释器。

| 执行 | 实际结果 | 退出码 |
| --- | --- | ---: |
| 标准库脚本 | 校验通过，覆盖 81 个文件、11 个主例、65 个控制变体及 1 个衍生 Oracle | 0 |
| 相关参考及静态回归 | 186 passed in 0.85s | 0 |
| M05 专项 | 10 passed in 0.33s | 0 |
| 全量，本地沙箱外 | 256 passed in 1.71s | 0 |

专项包含正常清单和九类临时副本异常。覆盖文件或预期指纹错误、控制输入指纹错误、错绑 Oracle、遗漏审阅指纹、未签收审批、测试节点不存在及执行日志删除。九项异常均得到退出码 1。[相关回归原始输出](G0_development_manifest_pytest.txt)

```bash
PYTHONPATH=src python -B -m pytest -q tests/test_g0_development_manifest.py -o addopts= -p no:cacheprovider
timeout 30s env PYTHONPATH=src python -B -m pytest -q -o addopts= -p no:cacheprovider
```

开发工作树的同日全量为 261 项通过，公开候选的 256 项对应公开树测试范围。执行证据属于本地 pytest。本人独立复核和正式批准仍待完成。

```text
0d5404b01e9b9ddd8d30a617e12119d308ac0dfe7f8afe853fdcbc886569a331  reference/regression_checks/G0_development_manifest.json
d01f1601e8668bf53579339629831ca7250e3bdf69327b30fc9d6b4d50ecd86f  reference/regression_checks/G0_development_manifest_pytest.txt
204ac4e23ec06c84dccf27c01016eb95b8865389b610a4eb96493f44ef3b762a  reference/regression_checks/check_g0_development_manifest.py
b1b6e8cfffcdcfae94a03dfab0f84d65fbb07fb461203256d3bf3c5397d41c97  tests/test_g0_development_manifest.py
```

## 本人签收增量的公开候选校验（2026-11-26）

A3-06、A3-08 v2 及其贡献分解已登记本人签收。回执绑定复核表、冻结输入和预期指纹。缺少回执或错用其他案例回执时，检查返回退出码 1。其余 9 个主例待确认。[签收回执](../manual_checks/G0_M05_user_confirmation.json)

公开候选基于 `5fb815d`，执行索引继续绑定上节的 186 项原始参考测试。本次在公开树校验 83 份证据，专项实际为 `12 passed in 0.40s`，沙箱外本地全量为 `258 passed in 1.67s`。三次退出码均为 0，使用上节所列命令及解释器环境。

```text
677c37fd8fd07c5a7847eb733dba3451cf4fd561c624ed92fdb616c5a03cf3bf  reference/regression_checks/G0_development_manifest.json
8cd3b75546e04bcea2858e5b4bbefa2151a44fc0dbb27517fb47a4fa63fd7b0d  reference/manual_checks/G0_M05_user_confirmation.json
6deb24d28b1ef77793d81609470055fa60c75f9e84edb278be6a4a8a9a7d18aa  reference/regression_checks/check_g0_development_manifest.py
3626354af59185efda9e23c35bac8d6a48c1b4ca94f958066920489ab5a11562  tests/test_g0_development_manifest.py
```

<a id="g0-release-evidence"></a>

## G0 放行公开候选复验（2026-11-26）

以公开提交 `cb247ff` 为父版本核对 G0 放行增量。11 个主例及 A3-08 v2 衍生贡献 Oracle 的签收回执均与冻结输入和预期一致。A3-09、A3-10 核验表保留本人确认状态和日期，公开版省略署名并重新绑定这两份表的指纹。执行索引继续绑定最初的 186 项参考回归记录，本次公开候选另行执行下表所列测试。[G0 放行登记](G0_fixture_coverage.md#g0-data-oracle-release) · [开发数据清单](G0_development_manifest.json)

| 执行 | 实际用时与结果 | 退出码 |
| --- | --- | ---: |
| 标准库清单校验 | 89 个文件、11 个主例、65 个控制变体、1 个衍生 Oracle 通过 | 0 |
| M05 专项 pytest | `12 passed in 0.37s` | 0 |
| 参考、静态 Fixture 与清单组合 pytest | `198 passed in 1.19s` | 0 |
| 公开候选全量 pytest，沙箱外 | `258 passed in 1.78s` | 0 |

执行环境为 CPython 3.10.12、pytest 9.1.1 和 Linux x86_64，命令中的 `python` 指该验证解释器。未确认批准、缺签收回执、回执错绑的拒绝控制均通过。本记录对应本地公开候选执行。

```bash
python3 -I -B reference/regression_checks/check_g0_development_manifest.py
PYTHONPATH=src python -B -m pytest -q tests/test_g0_development_manifest.py -o addopts= -p no:cacheprovider
PYTHONPATH=src python -B -m pytest -q tests/test_reference_cohort.py tests/test_reference_category_cohort.py tests/test_reference_channel_cohort.py tests/test_reference_region_cohort.py tests/test_reference_cross_domain_cohort.py tests/test_reference_contribution.py tests/test_reference_refund_dq.py tests/test_boundary_fixtures.py tests/test_g0_development_manifest.py -o addopts= -p no:cacheprovider
timeout 30s env PYTHONPATH=src python -B -m pytest -q -o addopts= -p no:cacheprovider
```

```text
2b5d030bf45189a5bba86dffa48eb8e79047d5ef2bb59df13337bcd470ea7cfb  reference/regression_checks/G0_development_manifest.json
6deb24d28b1ef77793d81609470055fa60c75f9e84edb278be6a4a8a9a7d18aa  reference/regression_checks/check_g0_development_manifest.py
903b09755d5d5d6ab0a870d0a1afbb03852975efc48cae5fe60132d235ea7b82  tests/test_g0_development_manifest.py
3b6fa46360edb5997e619b50d1335d28cfa24e25f75af861be4d07e94e5cffbb  reference/manual_checks/G0_M05_A3-09_user_confirmation.json
3a62a741e8af50ed3af7053a457d360d3de6a742156c6a10e5f9855661c6a060  reference/manual_checks/G0_M05_A3-10_user_confirmation.json
62fb6d02595398c84ae41cf3c4b2af21d5bc28466853921e37a01e1f80aff442  reference/manual_checks/G0_M05_remaining_user_confirmation.json
```

## M05 已有签收复验（2026-11-27）

对照开发工作树当前清单与本地公开提交 `40981cd`。三个条目逐项一致，按各自的 JSON 指针核验输入、冻结预期及签收条目的规范化 SHA-256，并核验两份 Fixture、贡献 Oracle、回执和复核表共五份文件的完整 SHA-256。三条绑定全部通过，完整输入与预期指纹见签收回执的 `cases`。清单 ID `A3-08` 指向修订 2，`M03-A3-08-v2` 使用同一输入，并绑定贡献 Oracle 自己的 `/expected`。[开发清单](G0_development_manifest.json) · [完整指纹及签收回执](../manual_checks/G0_M05_user_confirmation.json)

- **用户签收**记录于 2026-11-25 的回执，来源为 `explicit_user_confirmation`。回执中的三个对象分别匹配清单状态 `confirmed_by_user`、输入指纹和预期指纹。[签收回执](../manual_checks/G0_M05_user_confirmation.json)
- **独立子进程初算**由子进程依据原始输入和冻结规则完成，保存后由主进程对照 Oracle。初算署名、先后顺序和原稿指纹见既有复核表。本次仅核对证据绑定，沿用已有计算结果。[复核表](../manual_checks/G0_M05_independent_review.md)
- **L3** 仍缺本人独立实操与考核证据，沿用原登记状态。[个人能力核验项](../../docs/ROADMAP.md)

本节对应公开版开发清单，SHA-256 为 `2b5d030bf45189a5bba86dffa48eb8e79047d5ef2bb59df13337bcd470ea7cfb`。

## A3-02 与 A3-07 独立复核（2026-11-27）

当前清单的 11 个主例均已签收。优先案例 A3-09 和 A3-10 已完成，按指定备选取 A3-02 和 A3-07。初算只使用提取到独立目录的 `/input` 和 DD02 第 1、2 节，先保存本节初算台账再读取冻结预期。[开发数据清单](G0_development_manifest.json) · [DD02](../../docs/engineering/04_详细设计与实现准备/DataAgentX_DD02_指标数据与SQL工具_v1.2.md)

### 独立初算

两例均在 `domain_a` 的各自快照内，地区过滤为空。观察期为 7 天，基期为 `[09-01 00:00Z, 09-08 00:00Z)`，当前为 `[09-08 00:00Z, 09-15 00:00Z)`。下表日期为 2026 年，时间均已转换为 UTC。退款按完整订单键归属支付窗口，同单有多笔合格事件时只计一个退款订单。

| 输入 | 规范化 SHA-256 |
| --- | --- |
| A3-02 `/input` | `4f8410306b8bc4039212c2ace5e8340fca0acb08d305e2497cfa40f667f61711` |
| A3-07 `/input` | `cb458cfb0bc5555c8c680bab64885c0f2fd2e212951a12143260eb9ea3e339ca` |

#### A3-02 UTC 时间边界

`fixture_utc` 的支付时间由 `+08:00` 换算为 UTC，保留微秒。订单及退款事件的完整键均唯一，退款事件可关联到同域同快照订单。

| 订单 | 来源行 | 支付时间 | 观察截止 | 支付窗口 |
| --- | --- | --- | --- | --- |
| `U-BEFORE` | `u-row-before` | 08-31 23:59:59.999999 | 不适用 | 基期起点前 1 微秒 |
| `U-B-START` | `u-row-b-start` | 09-01 00:00:00 | 09-08 00:00:00 | 基期 |
| `U-B-LAST` | `u-row-b-last` | 09-07 23:59:59.999999 | 09-14 23:59:59.999999 | 基期 |
| `U-C-START` | `u-row-c-start` | 09-08 00:00:00 | 09-15 00:00:00 | 当前 |
| `U-C-LAST` | `u-row-c-last` | 09-14 23:59:59.999999 | 09-21 23:59:59.999999 | 当前 |
| `U-END` | `u-row-end` | 09-15 00:00:00 | 不适用 | 恰在当前窗结束，排除 |

| 退款事件 | 来源行 | 所属订单 | 退款时间 | 计数判断 |
| --- | --- | --- | --- | --- |
| `UR-1` | `u-refund-row-1` | `U-B-START` | 09-08 00:00:00 | 成功，恰在观察截止，计基期 |
| `UR-2` | `u-refund-row-2` | `U-B-LAST` | 09-15 00:00:00 | 成功，超过观察截止 1 微秒，排除 |
| `UR-3` | `u-refund-row-3` | `U-C-START` | 09-08 00:00:00 | 成功，恰在支付时刻，计当前 |
| `UR-4` | `u-refund-row-4` | `U-C-START` | 09-09 00:00:00 | 成功且在观察期内，与 `UR-3` 归并到同一退款订单 |
| `UR-5` | `u-refund-row-5` | `U-C-LAST` | 09-21 23:59:59.999999 | 恰在观察截止，状态为 `failed`，排除 |

基期与当前最晚观察截止分别为 09-14、09-21 的 23:59:59.999999，均不晚于 `as_of` 及退款水位 09-22 00:00。支付水位 09-15 00:00 覆盖两窗结束。结论为 `ready`。基期退款订单集合为 `{U-B-START}`，当前为 `{U-C-START}`，两窗均为 N=2、U=1、率 `1/2`，绝对与相对变化均为 `0`。

#### A3-07 同名类别 ID

`fixture_same_label_categories` 中，每笔订单以 `(domain_id, snapshot_id, product_id)` 唯一关联产品。`product_a → category_a`、`product_b → category_b`，两个类别在同域同快照目录中的展示名均为“图书”，分组键分别为 `(category, category_a)` 和 `(category, category_b)`。两笔成功退款分别为 `SR-B-B1`（`r07-refund-b-b1`，09-05）和 `SR-A-C1`（`r07-refund-a-c1`，09-11），由完整订单键分别关联 09-03 支付的 `S-B-B1` 和 09-09 支付的 `S-A-C1`，均落在各自的闭合观察期且不晚于 `as_of`。

| 支付窗 | 组 ID | 支付订单（来源行） | 退款订单 | N | U | 率 |
| --- | --- | --- | --- | ---: | ---: | ---: |
| 基期 | `category_a` | `S-A-B1`（`r07-row-a-b1`） | 无 | 1 | 0 | `0` |
| 基期 | `category_b` | `S-B-B1`（`r07-row-b-b1`） | `S-B-B1` | 1 | 1 | `1` |
| 基期 | 总计 | 本窗两组的并集 | `S-B-B1` | 2 | 1 | `1/2` |
| 当前 | `category_a` | `S-A-C1`（`r07-row-a-c1`）、`S-A-C2`（`r07-row-a-c2`） | `S-A-C1` | 2 | 1 | `1/2` |
| 当前 | `category_b` | `S-B-C1`（`r07-row-b-c1`）、`S-B-C2`（`r07-row-b-c2`） | 无 | 2 | 0 | `0` |
| 当前 | 总计 | 本窗两组的并集 | `S-A-C1` | 4 | 1 | `1/4` |

基期和当前最晚观察截止分别为 09-10、09-19 的 00:00，均不晚于 `as_of` 及退款水位 09-23 00:00。支付水位 09-15 00:00 覆盖两窗结束。业务键、退款关联、产品与类别关联均通过本例检查。两窗的组成员互斥并覆盖所有候选订单，各窗按组相加的 N/U 等于总计。结论为 `ready`，两窗总计的绝对变化为 `-1/4`（下降 25 个百分点），相对变化为 `-1/2`（下降 50%）。

### 冻结预期对照

独立初算正文先行保存。指纹覆盖从「独立初算」三级标题起至对照章节前的初算正文，保留正文最后一个换行。对照完成后复验同一段落的 SHA-256 为 `005731ac4ef8a96a74c22370d38a6e1a33342faf23904d194bf67d5bdf511ce9`。

| 案例 | 冻结 `/expected` 的规范化 SHA-256 | 对照结果 |
| --- | --- | --- |
| A3-02 | `6551c72bd346f34f71a15c1b95e898f5a27f461b7626990612ed81555d0b58e5` | 六个 UTC 支付时点、两窗订单来源集合、两个排除订单、五个退款事件的处置、退款订单集合、质量前提和发布指标全部一致。[冻结案例](../../tests/fixtures/order_boundaries/02_utc_boundaries.json) |
| A3-07 | `b9640a6dd7dbc73f1e50f94406659d3c869b7000f21282951c33f9e4a848a7e7` | 四条类别行和两条总计的身份及数值、订单来源、合格退款事件及对应订单、质量前提和分组守恒全部一致。[冻结案例](../../tests/fixtures/order_boundaries/07_same_label_distinct_category_ids.json) |

比较时把整数秒的 `.000000` 按同一 UTC 时点处理，把十进制率和分数转为精确有理数比较。逐项对照退出码为 `0`，未发现实质差异。本次为两例的独立补充复核。
