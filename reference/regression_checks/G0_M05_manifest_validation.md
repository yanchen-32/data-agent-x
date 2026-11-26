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
