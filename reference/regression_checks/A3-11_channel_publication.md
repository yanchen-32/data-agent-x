# A3-11渠道C01/C02：公开交付前验证

日期：2026-11-03。本次在公开独立历史[953e7ad](https://github.com/yanchen-32/data-agent-x/commit/953e7ad55d28c4d4182182d83bc4816ab2c4fb84)上追加渠道参考函数、C01/C02回归及证据，不合并旧开发历史。本文记录发布前实际验证，不能单凭文档内容当作远程推送成功凭据。

## 交付范围

新增[channel_cohort.py](../channel_cohort.py)、[渠道测试](../../tests/test_reference_channel_cohort.py)、[开发运行记录](A3-11_channel.md)、[最小复跑原始输出](A3-11_minimal_pytest.txt)及[实施起点核对](../manual_checks/A3-11_implementation_start.md)，并更新reference入口、ORACLE阶段说明和公开架构的渠道增量。公开架构保留原有生产/Provider排除边界，不整份覆盖为开发架构。

C01/C02已实际从input计算并对照先行冻结六行、Fraction、总体变化、渠道身份、来源、东南排除及分组守恒。基期N=3/U=1，当前N=4/U=3，绝对变化5/12。只在测试端读取expected，不生成或回填预期；四项既有冻结指纹保持不变。

C03～C07控制及C08展示名补强仍待后续；目录等防护分支存在不等于其全部拒绝路径已完成验收。未知渠道是当前参考范围限制，不宣称已实现完整非关键未知保留。未新增生产Runtime、授权、SQL、DQ状态映射、贡献或正式序列化，不以本次发布宣告G0或用户本人L3验收。

## 公开工作树实际执行

环境：CPython 3.10.12、pytest 9.1.1，公开分支工作树，显式PYTHONPATH=src。使用开发环境现有解释器；以下python指实际使用的该解释器，仅省略本机绝对路径，没有安装依赖。

渠道专项，退出码0：

```bash
PYTHONPATH=src python -B -m pytest tests/test_reference_channel_cohort.py -o addopts='' -q -p no:cacheprovider
```

```text
...                                                                      [100%]
3 passed in 0.06s
```

相关参考与静态检查，退出码0：

```bash
PYTHONPATH=src python -B -m pytest tests/test_reference_channel_cohort.py tests/test_reference_cohort.py tests/test_reference_category_cohort.py tests/test_boundary_fixtures.py -o addopts='' -q -p no:cacheprovider
```

```text
.......................................................................  [100%]
71 passed in 0.35s
```

全量检查，因既有沙箱内API/TestClient停滞问题获准在沙箱外本地执行，退出码0：

```bash
PYTHONPATH=src python -B -m pytest -o addopts='' -q -p no:cacheprovider
```

```text
........................................................................ [ 54%]
...........................................................              [100%]
131 passed in 0.58s
```

以上无失败。本轮未重新尝试沙箱内全量；未将历史收集失败或环境中断归到本次公开运行。131为实际公开工作树结果，不由开发136减去Provider推算；开发50项最小组合、71项相关及136项全量保留各自时点，不冒称本次结果。专项为相关/全量子集，数量不相加。

## 指纹、保护与发布方式

11号Fixture完整文件SHA-256为d652f050a45279f86b5900b76fdb1327ad9cefdaa114ad61a5d8e6457038f6f8；独立expected文件为c0e82fc22fb028235f249d524e516920b733636f7ad22ecbb53d7a7b6e811a7e。规范化input为459879d55d0ebbd0ed4103a628d1946d5e9c58f2aff7e8bbdbcf9804a4f85257，规范化expected为27479fab57016e1162c47d90fd7bbae465f8ac4d46ce77e061949db82b8a9b91；规范化方法沿用[冻结审核](../manual_checks/A3-11_freeze_review.md)。

新参考函数及测试分别保持207071252972bbd3cf6de22bc463fbd0c444068966cbb9cfd176b37f2d61629c、eb33e3775827d1bae1e822a15443df0c30aa6499b863d95d477b149e07ebe804，与开发回归记录一致。冻结数据、既有总体/类别函数、旧测试、生产包、Provider及内部归档均不随本次提交改变。

本次仅准备明确清单的公开增量、检查引用及暂存差异，基于公开父提交追加提交，再以正常快进、原子方式推送main和release/public-v1.2.1；远程位置以推送后git ls-remote实查为准，不强推。旧创建阶段文档的“未提交/未推送”是当时快照，不追溯改写。

本地公开工作树pytest不是CI、GitHub Actions或用户L3。当前开发未提交工作保留，路线图未据此标记完成。
