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
