# A3-03 历史验收证据核对

2026-11-26（Asia/Shanghai）核对 2026-10-16 既有记录。**A3-03 本人签收保持 `pending_user_confirmation`。** 案例版本可对应，仍缺可归属于用户本人的 A3-03 独立复核结论或签收确认。[开发数据清单](G0_development_manifest.json)

## 可绑定的版本与证据

案例为 A3-03，Fixture 格式版本 `1`，基线 `DAX-RB-1.2.1`，快照 `fixture_duplicate`。当前 Fixture 与 10 月 13 日引入版本 `9b6ca92`、10 月 15 日提交 `468882b` 和公开提交 `cb247ff` 逐字节一致。10 月 15 日提交的 Oracle A3-03 章节与当前章节内容一致。[冻结 Fixture](../../tests/fixtures/order_boundaries/03_duplicate_orders.json) · [人工 Oracle](../../tests/fixtures/order_boundaries/ORACLE.md)

| 对象 | SHA-256 |
| --- | --- |
| Fixture 全文 | `606d0c0aefaa385a59c81222e70f779a3a652af97c5bf27c17c8a26a5e0b85a7` |
| `/input` 规范化 JSON | `3dedc50609d23226a5b794c62478d884a793978abda7b30bced61220398f35a9` |
| `/expected` 规范化 JSON | `ab5dab62e0b4c4d1fdec4fa151aa51a2153d74a60b952b411310d99fc06a10ef` |
| Oracle 的 A3-03 章节 | `da8f63b3a945cf405cc079e6843a43c2290f08eb2cb017004c294df8fa7cc609` |

冻结 Oracle 记录一个重复业务键 `(domain_a, fixture_duplicate, D-B)`，涉及来源行 `d-row-1`、`d-row-2`。冻结业务预期为 `blocked_by_quality`，双窗指标和变化均为 `null`。现有回归日志确认参考函数拒绝重复键的 `ValueError` 断言已通过。以上沿用原有业务预期和技术执行证据。[技术回归日志](G0_development_manifest_pytest.txt)

## 本人签收证据缺口

- 仓库中可定位的 10 月 16 日记录为 A3-04、A3-05 的技术回归。10 月 14 日逐单复核的范围为 A3-01、A3-02，其中记录的重复订单检查来自自动测试。[10 月 16 日回归记录](A3-04_A3-05.md) · [10 月 14 日复核](../manual_checks/2026-10-14.md)
- 在已核对的 10 月 16 日项目验收材料及 Git 历史中，未定位到用户本人对 A3-03 的初算结论或签收确认。当前 M05 签收回执覆盖 A3-06、A3-08 v2 及其贡献 Oracle。[已有签收回执](../manual_checks/G0_M05_user_confirmation.json)
- 待补的证据是可归属于用户本人的 A3-03 独立复核原记录或明确确认，以及其中足以对齐本例冻结版本的结论和版本线索。待核对通过后再登记历史签收。本轮只核验既有文档和指纹，未启动参考计算或新的盲算。

## 当前冻结版本签收补记（2026-11-26）

用户随后明确确认 A3-03 当前冻结版本及复核结论，并授权登记本人签收。清单以此次确认及上列输入、预期指纹登记为 `confirmed_by_user`。10 月 16 日的历史本人证据仍待定位。[当前版本回执](../manual_checks/G0_M05_remaining_user_confirmation.json)
