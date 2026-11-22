# M03 最小贡献参考层 Must 关闭登记

2026-11-22（Asia/Shanghai）。**M03 最小贡献参考层 Must 已关闭。** 本次复验直接使用 A3-08v2 原始输入的参考聚合，并对照先行人工台账转录的冻结 Oracle。下列贡献均为精确比例差。[冻结贡献 Oracle](../manual_checks/G0_M03_A3-08_v2_contribution_expected.json) · [参考函数](../contribution.py) · [专项测试](../../tests/test_reference_contribution.py)

| 项目 | 冻结值 | 核对结果 |
| --- | ---: | --- |
| 共享 A 的 `within` | `3/8` | 一致 |
| 共享 A 的 `structure` | `-1/8` | 一致 |
| 退出 B 的 `exit` | `-1/2` | 一致 |
| 新增 C 的 `entry` | `3/4` | 一致 |
| A、B、C 各组净贡献 | `1/4`、`-1/2`、`3/4` | 逐组一致 |
| 四项之和与总体变化 | `1/2`，总体率 `1/2 → 1` | 逐项及总和一致 |
| 精确残差 | `0` | 等于 `Fraction(0)` |

固定正例逐组检查权重、组率、加权率、适用贡献和净贡献的 `Fraction` 类型与值。生命周期精确匹配 `shared={A}`、`exit={B}`、`entry={C}`。B 仅有基期，C 仅有当前，字典比较会检出补造的窗口或数值。A 基期的正分母零退款率保留为真实的 `Fraction(0)`。专项比较调用前后的输入，且更改返回结果后再次比较输入，确认结果对象与聚合输入隔离。Fixture 与 Oracle 在用例执行前后逐字节一致。

| 拒绝条件 | 本轮通过的控制 |
| --- | --- |
| 总体分母为零 | `ready[baseline]` 和 `ready[current]` 分别构造基期与当前零分母，均抛出 `ValueError` |
| 组身份或总计行重复 | `duplicate-group-id` 更换重复组的展示名仍拒绝，`duplicate-total` 拒绝重复总计 |
| N 或 U 不守恒 | `N-only` 与 `U-only` 分别只改变一类计数，行数保持齐全。缺组、缺总计及总计冲突另有拒绝用例 |
| 上游不可比或结果不完整 | 显式不可比、成熟或水位不满足、`complete=False` 及 `truncated=True` 均抛出 `ValueError`，调用没有可发布的完整贡献结果 |

## 实际执行及版本

本地开发工作树使用 CPython 3.10.12、pytest 9.1.1。专项 **29 项**通过，用时 0.05 秒。相关参考回归 **182 项**通过，用时 0.81 秒。两轮退出码均为 `0`，相关回归已包含专项。原始 stdout、退出码、解释器及执行文件的 SHA-256 均已保存。记录 SHA-256 为 `2c3132799d8cfcf0f8c4352830b97d8c16ceee72392c7854827b36091236a1fa`。[本轮执行记录](G0_M03_Must_closure_pytest.txt)

```bash
PYTHONPATH=src .venv/bin/python -B -m pytest tests/test_reference_contribution.py -rA -o addopts= -q -p no:cacheprovider
PYTHONPATH=src .venv/bin/python -B -m pytest tests/test_reference_contribution.py tests/test_reference_cohort.py tests/test_reference_category_cohort.py tests/test_reference_channel_cohort.py tests/test_reference_region_cohort.py tests/test_reference_cross_domain_cohort.py tests/test_boundary_fixtures.py -o addopts= -q -p no:cacheprovider
```

执行前核对 Oracle 的八份来源、规范化输入及 Scope，绑定源码、现有测试及冻结数据均与公开提交 `7d509cd` 逐字节一致。`pyproject.toml` 使用既有开发配置。全部绑定文件的执行前后指纹一致。[公开实现提交](https://github.com/yanchen-32/data-agent-x/commit/7d509cdea8bf4c5b3f7c53e045513c214b074f1c)

关闭范围限于受控合成数据的最小贡献参考层。生产 `analysis.run` 的授权证据、同 Scope 校验、查询完整性与截断证明、正式序列化和 PostgreSQL 权限验证由 M06 验收。G0 整体验收独立登记。[输入契约核查](G0_M03_input_contract.md) · [覆盖矩阵](G0_fixture_coverage.md)
