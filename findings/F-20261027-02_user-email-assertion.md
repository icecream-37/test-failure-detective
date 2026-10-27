# [F-20261027-02] 用户邮箱字段不符合格式断言

| 字段 | 内容 |
|------|------|
| 日期 | 2026-10-27 |
| 环境 | 本地，Python 3.12；对演示 API `/users/1` |
| 严重级别 | P2 |
| 状态 | 已确认 |
| 来源日志 | `samples/assertion_failed.txt` |
| 工具分类 | `assertion`（断言失败） |
| 置信度 | 90% |
| 命中规则 | `assert_error` |

## 现象

`test_get_user_email_format` 失败：响应 200，但 `email` 为 `invalid-email-value`，不包含 `@`。

## 日志证据

```
assert "@" in body["email"]
AssertionError: assert '@' in 'invalid-email-value'
tests/test_users_api.py:41: AssertionError
```

## 工具分类结果

- 类别：断言失败
- 机器建议：对照 expected vs actual：确认是产品缺陷还是断言过严/过时。
- 是否同意：**是**（归类正确；根因需人工定）

## 人工结论

根因类型：**产品缺陷（或演示数据污染）** — 待开发确认

验证：手工 GET 同路径，status=200，body.email 确为非法字符串；断言本身合理（邮箱应含 `@`）。  
已排除：环境连通、依赖缺失。下一步是提单给接口负责人，并附完整 JSON。

## 复现步骤

1. `GET /users/1`
2. 检查 `email` 字段
3. 期望：合法邮箱；实际：`invalid-email-value`

## 建议

- 开缺陷单：字段校验缺失或造数错误
- 用例保留；可在报告中附响应 body 片段，避免开发只看到 assert 一行
- 若属演示环境脏数据，改为夹具注入可控用户后再断言

## 关联

- 用例：`tests/test_users_api.py::test_get_user_email_format`
- 同类项目：可与 api-regression-jsonplaceholder 的契约检查互补
