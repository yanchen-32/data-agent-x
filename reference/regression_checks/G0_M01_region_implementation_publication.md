# M01-region：规则、冻结Oracle与最小入口公开交付

日期：2026-11-10（Asia/Shanghai）。基于公开父提交[2fe6d51](https://github.com/yanchen-32/data-agent-x/commit/2fe6d51d9c1f0797b09930b875a47e4f70f2ada6)追加交付。本文记录实际公开工作树验证，远程是否更新须另以推送结果及git ls-remote核验，不单凭文档判成功。

## 本次范围与状态

- [规则审定v1](../manual_checks/G0_M01_region_rule_review.md)、[冻结Oracle](../manual_checks/G0_M01_region_expected.json)及[冻结记录](../manual_checks/G0_M01_region_freeze_review.md)一同交付，原字节不改；RG01.W/RG02.A完整业务预期已冻结，40项变体登记中的其余控制不因此全部具有已冻结输出或执行证据。
- [最小入口](../region_cohort.py)只依赖标准库和总体参考接口，复用队列/成熟水位，独立以完整订单键去重退款并按region_id分组；不依赖类别/渠道/生产业务代码，不修改输入。未知数据归组的授权前提由调用侧预审，函数不新增权限开关或证明真实授权。
- [当前地区测试](../../tests/test_reference_region_cohort.py)保留RG01/02两项参数化，强化完整键退款事件回查、整体来源、SE排除和Fraction断言。W四行与A六行均匹配先行Oracle；单地区Scope仍只是总计的单组退化表达。
- [开发阶段记录](G0_M01_region.md)、[最初开发输出](G0_M01_region_pytest.txt)和[RG01/02开发复跑](G0_M01_region_RG01_RG02_pytest.txt)保留原字节/原版本对应关系；早期测试f0023995与当前46706e3d分开，开发188项不改称公开结果。
- 公开架构仅追加region当前能力并同步本次公开验证，reference入口及G0矩阵追加对应进展；既有公开前缀及脱敏差异保留。个人G0记录、内部完整开发清单、Provider工作、内部归档及旧开发Git历史不上传。

本次没有修改既有总体/类别/渠道参考实现、生产Runtime、依赖、原Fixture或旧expected，也未重新生成冻结Oracle。仅固定正常输入及代表性控制通过；完整RG03～RG06与三维共同Scope仍待实际验收，**M01/G0保持开放，C08仍为非阻塞Should**。技术冻结/本地计算通过不代替用户本人签字、生产批准或真实授权。

## 实际公开工作树回归

环境：CPython 3.10.12、pytest 9.1.1、Linux x86_64；复用既有虚拟环境解释器，PYTHONPATH=src，没有安装依赖。实际命令、逐项身份、退出码和完整输出见[G0_M01_region_public_pytest.txt](G0_M01_region_public_pytest.txt)，三阶段顺序执行，前一步通过才进入下一步。

| 范围 | 实际结果 | 退出码 |
| --- | --- | --- |
| 公开地区专项，附-rA | 13 passed in 0.18s | 0 |
| 公开region＋总体＋类别＋渠道＋静态Fixture | 123 passed in 0.55s | 0 |
| 公开工作树全量pytest | 183 passed in 0.60s | 0 |

13项中包含RG01/RG02两项，不能相加；123包含region13+总体9+类别38+渠道42+静态21，专项和相关都是全量子集。183来自本轮真实输出，不根据开发188项加减推算。本次无失败，无答案修订。

全量因已知API/TestClient沙箱内停滞限制获准在沙箱外本地执行，没有新增沙箱内全量尝试。**所有结果均为本地公开工作树pytest，不是GitHub Actions CI、用户本人L3或生产授权验证。** 本轮未查询或声称CI通过，测试矩阵仍是计划而非执行结果。

## 源码与冻结指纹绑定

[公开版本清单](G0_M01_region_public_manifest.json)绑定53份实际运行源码/测试/输入/规则/配置文件，包含父提交、逐文件SHA-256、冻结规则/Oracle和历史开发输出范围。提交后再次核对提交树中的53份文件均与清单一致，使执行证据对应最终追加版本，不将父提交当作已含本次实现。

| 对象 | SHA-256 |
| --- | --- |
| 当前region实现 | 4652685bd2a104a047a09e62b8eb26c9aa400330fb1a2268bce4e00987c15dba |
| 当前地区测试 | 46706e3d95600b25a75198e6aada7d6ecb8e262a27d6e5c8882c07c3b75ac6f9 |
| 冻结Oracle完整文件 | 50bca606d29077276d7a5d39c0c55dc0fbd57cfa5a0ff836db953bd9e301b1ce |
| 规则审定v1完整文件 | 5322018b50b74da02b32c888b6777e9527fecd84b58d66b4a752ed664343c96c |
| 公开53文件源码映射 | 8d4629116144a115882970078129ded3d00151876fda6581624bd2f81b8083bf |
| 公开版本清单完整文件 | 20bf4e8eeace6ffaa9ec025ecf70d24fa542396be6ab0c62bc4a0690baeddcef |
| 本轮公开输出 | bc48d5c8a1e0c444628a99156e603a843e261694d041c513811131881da7057b |

源码映射规范化为UTF-8编码的json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))，无末尾换行。运行前后53份文件字节不变，原45份公开基线运行文件亦未变，原11号Fixture仍为d652f050a45279f86b5900b76fdb1327ad9cefdaa114ad61a5d8e6457038f6f8。

规则/冻结记录及此前开发阶段的“尚未提交、未跑公开”等文字保留原时点，本次交付及公开复跑由本文和新清单补充；不追溯改写旧证据。该清单仅为执行版本绑定，不是批准的dataset_manifest或正式盲测集。

发布沿公开独立历史追加，正常原子快进main与release/public-v1.2.1后再核对远程SHA，不改写历史，不移动或破坏旧开发main及其未提交成果。

暂存空白检查仅报告旧RG01/RG02原始输出末尾保留的空行；为保持7fcce42d对应的原始证据字节不裁剪。只排除blank-at-eof后其余git diff --cached --check通过，不修改冻结JSON或原输出。
