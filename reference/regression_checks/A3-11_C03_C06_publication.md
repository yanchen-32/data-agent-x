# A3-11 C03～C06：公开交付前验证

日期：2026-11-05。本次以公开独立历史[c9b8536](https://github.com/yanchen-32/data-agent-x/commit/c9b8536a6d26287a845a978f0cd59f4b99a79169)为父提交准备追加发布，只迁移控制测试、独立控制预期、执行证据及文档覆盖增量。本文记录发布前实际验证，不单凭文档内容认定远程推送成功。

## 发布内容及范围

- C03：全地区深拷贝对照，验证先行漏过滤反例、东南新增来源及两种Scope的分组守恒。
- C04：目录重复、域/快照混入及过滤外订单的关键产品关联拒绝，并保留合法非关键类别未知。
- C05：[独立控制预期](../manual_checks/A3-11_C05_expected.json)和[依据](../manual_checks/A3-11_C05_expected.md)，覆盖四类不足、三个等号允许及合法基期零退款。
- C06：[事件及独立预期](../manual_checks/A3-11_C06_expected.json)和[依据](../manual_checks/A3-11_C06_expected.md)，沿用已发布C06定义，覆盖四类事件×双窗；as_of后样例也在H后，不声称孤立验证as_of。
- [当前渠道测试](../../tests/test_reference_channel_cohort.py)、[分阶段回归记录](A3-11_channel.md)、C03/C04/C05/C06原始输出、既有控制全量归档及C05新复跑证据，保留各批次时点、范围和SHA-256。
- reference入口及公开架构渠道覆盖段同步到C01～C06共34项，C07和C08仍待后续。

不复制开发架构中的未公开Provider/环境说明，不改变公开架构其余有意差异。生产包、总体/类别/渠道参考函数、原11号Fixture及A3-11_expected.json不变；只新增C05/C06独立控制记录，不依据actual回填主预期。旧开发历史、内部归档及本地分支详情记录不进入公开提交。

## 公开工作树实际执行

环境：CPython 3.10.12、pytest 9.1.1，公开分支工作树，显式PYTHONPATH=src。使用现有开发解释器，以下python指该已验证解释器并仅省略本机绝对路径；没有安装依赖。

渠道专项，实际退出码0：

```bash
PYTHONPATH=src python -B -m pytest tests/test_reference_channel_cohort.py -o addopts='' -q -p no:cacheprovider
```

```text
..................................                                       [100%]
34 passed in 0.20s
```

相关参考与静态，实际退出码0：

```bash
PYTHONPATH=src python -B -m pytest tests/test_reference_channel_cohort.py tests/test_reference_cohort.py tests/test_reference_category_cohort.py tests/test_boundary_fixtures.py -o addopts='' -q -p no:cacheprovider
```

```text
........................................................................ [ 70%]
..............................                                           [100%]
102 passed in 0.49s
```

全量，因既有沙箱内API/TestClient停滞问题获准在沙箱外本地执行，实际退出码0：

```bash
PYTHONPATH=src python -B -m pytest -o addopts='' -q -p no:cacheprovider
```

```text
........................................................................ [ 44%]
........................................................................ [ 88%]
..................                                                       [100%]
162 passed in 0.57s
```

本轮无失败，也没有新的沙箱内全量尝试。162是此次公开工作树实际运行结果，不从开发或旧公开数量加减推算。34项包含原C01/C02三项及C03～C06三十一项；102项含渠道34、总体9、类别38、静态21，专项为全量子集，不相加。

开发记录中的151项全量、C05相关94项及其他旧结果均保留原时点；上述新结果不是替换旧摘要。公开工作树运行仍是本地pytest，**不是GitHub Actions CI、用户本人L3或独立人工验收**。

## 指纹与保护

11号Fixture完整文件SHA-256为d652f050a45279f86b5900b76fdb1327ad9cefdaa114ad61a5d8e6457038f6f8；原独立expected为c0e82fc22fb028235f249d524e516920b733636f7ad22ecbb53d7a7b6e811a7e；规范化input/expected分别为459879d55d0ebbd0ed4103a628d1946d5e9c58f2aff7e8bbdbcf9804a4f85257、27479fab57016e1162c47d90fd7bbae465f8ac4d46ce77e061949db82b8a9b91。C05/C06控制预期文件分别为cbe71efb6734e3480f5d1ad93793d4338c240377dec5cb3335c01136c7565819、32ecd37ddf05767c5496362c8f0f3529d8a905412cd6c1b78ae8d8a42c52ae03；复制到公开工作树后均不改。

当前渠道测试文件指纹为5441075b1bfb3da7cff63d1f825b74023b383230b2e26e4e41ee2cc947d667d4，渠道实现仍为207071252972bbd3cf6de22bc463fbd0c444068966cbb9cfd176b37f2d61629c。历史证据文件保留原字节和原测试版本对应关系，不因当前套件增大而覆盖旧数量。

发布前核对明确清单、引用、敏感路径、冻结文件及暂存差异；基于公开父提交追加提交，正常快进原子推送main及release/public-v1.2.1，再通过git ls-remote核对远程SHA，不改写历史。旧创建/归档记录中的“未提交/未推送”仅对应当时快照，不追溯改写。

本次不更新路线图完成状态，不因控制通过宣称生产DQ、SQL、授权、贡献或G0已验收。
