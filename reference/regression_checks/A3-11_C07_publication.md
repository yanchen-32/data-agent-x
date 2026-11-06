# A3-11 C07与最小渠道参考Must：公开交付验证

日期：2026-11-06（Asia/Shanghai）。基于公开独立父提交[91e215d](https://github.com/yanchen-32/data-agent-x/commit/91e215d5423ca766e6af6768566af4cd79ee9a8f)准备追加交付，包含C07输入隔离/逐列表与联合重排、既有本地回归证据及C01～C07 Must逐项评审。本文记录实际公开工作树验证；不单凭文档内容认定远程推送完成。

## 内容及公开边界

- [渠道测试](../../tests/test_reference_channel_cohort.py)与已评审开发文件完全一致，SHA-256为`d4fb4abaf6ade2d2fadbf20385943011e02db9b3e015a90b66da452712477817`。C07为返回值/交错Scope隔离1项，加订单、退款、产品、类别、渠道、地区分别逆序及联合逆序7项；候选订单仅比较集合，单行产品/类别目录仅在深拷贝中补合法未引用项后重排。
- 保留[C07初次输出](A3-11_C07_pytest.txt)、[重排补强输出](A3-11_C07_reordering_pytest.txt)和[开发完整回归输出](A3-11_full_regression_pytest.txt)原字节。开发175项仍只属于原开发树，不替换为本次公开170项。
- 原完整47文件开发清单含未公开工作信息，保留本地；公开的是另建的[版本摘要](A3-11_full_regression_public_manifest.json)，包含45份实际公开运行文件、冻结绑定、环境、公开结果及原开发清单的哈希承诺，不复制内部HEAD或未公开文件详情。原开发清单文件SHA-256仍为d36dd5038414f248b9868aeb7bac91daf6baad11249e9978730b7d93a462cced。
- Must评审、渠道记录、G0矩阵和入口中的清单链接调整为该公开摘要，并明确原开发证据的历史范围；原完整清单与开发记录保留本地原文。公开架构仅同步渠道覆盖及当前公开验证，不迁移开发架构中的其他差异。
- 三个参考函数、生产包、11号主Fixture、独立expected及C05/C06冻结控制预期均未因本次交付修改。未上传旧开发历史、内部归档、环境同步日志或未公开Provider工作。

## 实际公开工作树执行

环境：CPython 3.10.12、pytest 9.1.1、Linux x86_64；复用现有虚拟环境解释器，PYTHONPATH=src，没有安装依赖。完整实际命令和输出见[A3-11_C07_public_pytest.txt](A3-11_C07_public_pytest.txt)，专项-rA列出42条PASSED身份。三阶段按以下顺序执行，前一步通过才执行下一步。

| 顺序 | 范围 | 实际结果 | 退出码 |
| --- | --- | --- | --- |
| 1 | 公开渠道专项 | 42 passed in 0.22s | 0 |
| 2 | 公开渠道＋总体＋类别＋静态Fixture | 110 passed in 0.48s | 0 |
| 3 | 公开工作树全量pytest | 170 passed in 0.56s | 0 |

全量因已知沙箱内API/TestClient限制获准在沙箱外本地执行；未新增沙箱内全量尝试。此次无失败，无需修复计算器或调整冻结预期。专项和相关均为全量子集，不相加；数量来自本轮实际输出，不以开发175项作加减推算。

三阶段均是**本地公开工作树pytest，不是GitHub Actions CI、用户本人L3或独立人工签收**。没有运行或查询CI。

## 版本绑定与文件保护

| 对象 | SHA-256 |
| --- | --- |
| 公开45文件源码映射 | d450cae0795ed6297f7d478f12b07245275d6b5018ceaf70aea4432305a10d74 |
| 公开版本摘要完整文件 | 3a913406adffefb1b2322f64fe43348fb59c684754b8ff7a5521d5c2f0adde45 |
| 本次公开pytest输出 | 59c9369a0cdcca71395ace6d71107582ee436608fd18ac5bb465e1bf046ba480 |
| 11号主Fixture完整文件 | d652f050a45279f86b5900b76fdb1327ad9cefdaa114ad61a5d8e6457038f6f8 |
| 原独立expected完整文件 | c0e82fc22fb028235f249d524e516920b733636f7ad22ecbb53d7a7b6e811a7e |

45文件映射使用UTF-8编码的json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))，无末尾换行。运行前后逐文件核对完全一致；主input/expected规范化哈希、C05/C06预期、参考函数绑定均保存在公开摘要，主冻结文件与父提交逐字节一致。提交后再次按摘要核对提交树中的文件字节，使执行证据对应最终交付版本；文档不嵌入自身提交号，避免循环绑定。

## Must关闭与剩余状态

C01～C07实际通过数量为1/2/1/14/8/8/8，共42项，与[逐项评审](A3-11_Must_review.md)一致；本次公开复跑确认相同C07代码和冻结契约在公开工作树中无回归。仅关闭A3-11最小渠道参考Must，C08仍为Should。G0 M01仅获得渠道子项证据，region及其他G0 Must、生产DQ/授权SQL/QueryEvidence、贡献及正式评测仍不关闭，也不代替本人验收。

此次从公开独立历史追加提交，正常原子推送main与release/public-v1.2.1，再以git ls-remote核验两者SHA；不改写历史或同步旧开发main。前期记录中的“尚未提交/未推送/未跑公开工作树”保留其阶段含义，本节补充后续公开交付验证。

暂存空白检查仅在两份原始C07输出末尾报告历史保留的空行；为保持原SHA-256不裁剪证据字节。使用git -c core.whitespace=-blank-at-eof diff --cached --check只排除该项后，其余空白检查通过。
