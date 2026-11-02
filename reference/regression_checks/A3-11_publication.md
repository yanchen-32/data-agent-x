# G0覆盖审查与A3-11：公开交付前验证记录

日期：2026-11-02。基于公开独立历史的父提交[d7b702a](https://github.com/yanchen-32/data-agent-x/commit/d7b702a6ea517d5e3e0ff437d39c714e8155023c)准备追加发布；不合并旧开发分支历史，不包含内部归档、环境同步日志、Provider或其他未提交实现。本记录保存发布前实际验证证据，不将文档本身当作远程推送成功凭据。

## 交付范围与当前状态

- [G0矩阵](G0_fixture_coverage.md)及[清单](G0_fixture_inventory.json)：保留十主例审查快照及Must/Should缺口，不因后续主例增至11宣告G0放行。
- [A3-10验收状态核对](A3-10_acceptance.md)：补充矩阵所引用的技术证据，保留其创建时点及历史执行限制，不改旧红绿灯记录。
- A3-11[设计](../manual_checks/A3-11_design.md)、[原始输入草案](../fixture_drafts/11_single_region_channel_grouping.json)及[台账初稿](../manual_checks/A3-11_expected_draft.md)：作为先行来源原字节保存，不因已冻结而改写草稿历史。
- A3-11[输入复核](../manual_checks/A3-11_input_review.md)、[独立expected](../manual_checks/A3-11_expected.json)、[固定Fixture](../../tests/fixtures/order_boundaries/11_single_region_channel_grouping.json)及[冻结审核](../manual_checks/A3-11_freeze_review.md)：开发Oracle v1已冻结，六条行、Fraction、来源、守恒、漏过滤反例及指纹有先行依据，无数值或来源修订。
- [渠道Oracle实施方案](../manual_checks/A3-11_channel_oracle_plan.md)：复用总体成熟/支付队列，独立渠道分组的输入/输出契约及测试清单；尚未实施，不提前产生actual或回填expected。
- 更新reference入口、ORACLE说明及既有静态Fixture文件清单。channels计算器和渠道计算回归均未新增，生产Runtime及总体/类别函数不变。

本地分支详情的进度核对记录保留在开发工作树，不进入公开提交。各创建阶段文档中的“未提交/未推送”描述为当时快照，不代表后续发布操作的状态；其内容不追溯改写。生产批准、正式盲测、用户本人验收、G0其余Must均不因本次发布完成。

## 公开工作树实际验证

实际在公开分支工作树运行，使用开发环境现有解释器，CPython 3.10.12、pytest 9.1.1，显式PYTHONPATH=src，避免把开发树可编辑安装当作公开源码。下列命令的python指该已验证解释器，省略本机绝对路径；没有新增或安装依赖。

相关检查：

```bash
PYTHONPATH=src python -B -m pytest tests/test_reference_category_cohort.py tests/test_reference_cohort.py tests/test_boundary_fixtures.py -o addopts='' -q -p no:cacheprovider
```

```text
....................................................................     [100%]
68 passed in 0.32s
```

退出码0，范围为38项类别参考、9项总体参考、21项静态Fixture检查。A3-11仅新增通用静态登记，不把相关68项声称为渠道实际计算回归。

全量检查：

```bash
PYTHONPATH=src python -B -m pytest -o addopts='' -q -p no:cacheprovider
```

第一次沙箱内运行只输出部分进度后停滞，手动中断退出130，未登记为通过。随后在沙箱外本地重跑同一命令，实际退出码0：

```text
........................................................................ [ 56%]
........................................................                 [100%]
128 passed in 0.50s
```

128是公开工作树实际收集与运行的数量，未从开发树结果减去Provider测试推算。以上是本地验证，不是GitHub Actions或CI；未查询、触发或推定CI结论。旧开发/公开执行记录均保留各自时点，不冒充本轮结果。

## 冻结保护与交付核对

固定Fixture SHA-256为d652f050a45279f86b5900b76fdb1327ad9cefdaa114ad61a5d8e6457038f6f8；独立预期记录为c0e82fc22fb028235f249d524e516920b733636f7ad22ecbb53d7a7b6e811a7e；规范化input为459879d55d0ebbd0ed4103a628d1946d5e9c58f2aff7e8bbdbcf9804a4f85257。复制到公开工作树不改上述字节或数值；没有用测试输出更新预期。

发布前检查引用文件、提交清单、敏感本机路径、旧文件差异及git diff --check；检查后才暂存明确文件并基于公开父提交生成追加提交。远程仅以正常快进推送更新main及release/public-v1.2.1，不改写历史；推送后另用git ls-remote核对两个分支SHA。若远程并发变化，须重新核对，不能强推跳过。

独立渠道参考计算及固定回归仍是下一步；本记录未实现或验收生产SQL、真实授权、DQ状态映射、贡献或正式输出序列化。
