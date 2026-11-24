# G0 M02 最小合法跨域参考层关闭登记

依据 DD02 及公开提交 8330c68 的冻结双 Scope 正例完成关闭评审。两域共享局部 ID 和展示名称，反转产品类别映射，完整事实键仍含 domain_id 和 snapshot_id。两域分别调用类别参考入口，专项校验六条聚合行、精确分数、来源与分组守恒。[冻结输入和预期](../manual_checks/G0_M02_cross_domain_expected.json) · [公开参考提交](https://github.com/yanchen-32/data-agent-x/commit/8330c68e206496bd3b5200ee1c83a90688dec011)

## 关闭登记（2026-11-20）

**M02 最小合法跨域参考层 Must 已关闭。** 两个合法 Scope 独立对照冻结 Oracle，检查完整订单与退款键、支付与退款来源及分组守恒。`A→B→A` 和 `B→A→B` 每步各自对照冻结预期，并检查先前返回值，验证交错调用无串数。[专项测试](../../tests/test_reference_cross_domain_cohort.py)

登记引用 11 月 17 日的执行证据。M02 专项 4 项通过，公开候选相关回归 153 项、全量回归 213 项通过，三次退出码均为 0。执行证据绑定公开提交 `8330c68`。[专项输出](G0_M02_cross_domain_pytest.txt) · [公开候选输出](G0_M02_public_pytest.txt) · [版本清单](G0_M02_public_manifest.json)

真实 PostgreSQL 角色、授权视图、SQL 域隔离及权限探针仍由 M06 验收。同域不同快照的合法配对属于本次范围之外，G0 整体验收仍待完成。[覆盖矩阵](G0_fixture_coverage.md)

### 当前参考版本复核（2026-11-24）

M04 更新了总体参考入口。按公开提交 `a479fad` 核对本次运行文件后，复用原专项再次验证两域独立结果与 `A→B→A`、`B→A→B`。四项均通过，分组与订单、退款及来源断言继续匹配双 Scope 冻结 Oracle。原专项、Oracle、两份输入及历史执行输出的指纹仍与既有清单一致。[冻结 Oracle](../manual_checks/G0_M02_cross_domain_expected.json) · [既有版本清单](G0_M02_public_manifest.json)

```text
PYTHONPATH=src .venv/bin/python -B -m pytest tests/test_reference_cross_domain_cohort.py -rA -o addopts= -q -p no:cacheprovider
4 passed in 0.32s
退出码：0
```

本次参考入口 `reference/cohort.py` 的 SHA-256 为 `596bbce438326ad3f4f537c20a78b80190a36efde4cd97983eff8417e84cb1b3`。维持 M02 最小合法跨域参考层局部关闭，实际 PostgreSQL 权限仍由 M06 验收。
