# findings/ — 测试发现归档

这里才是**测试产出**：不是「模型说了句分类」，而是测试同学确认后的可跟踪记录。

## 推荐闭环

1. `python -m failure_detective path/to/ci.log --out out/`
2. 打开 `out/report.html`，按类别排障
3. 对确认的问题：
   - 复制 `FINDING_TEMPLATE.md`，或
   - 加 `--emit-finding-stub` 生成草稿再改
4. 填「人工结论 / 复现 / 建议」，改状态为已确认或已提单

## 本目录示例

| 文件 | 说明 |
|------|------|
| `FINDING_TEMPLATE.md` | 空模板 |
| `F-20261027-01_*.md` | 环境类：Connection refused |
| `F-20261027-02_*.md` | 断言类：邮箱格式 |
| `F-20261027-03_*.md` | Flaky：结算按钮重试通过 |

面试时可打开任意一份，讲「我怎么从失败日志落到可跟踪问题」。
