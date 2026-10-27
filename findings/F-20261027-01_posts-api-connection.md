# [F-20261027-01] posts API 连不上本地服务（Connection refused）

| 字段 | 内容 |
|------|------|
| 日期 | 2026-10-27 |
| 环境 | GitHub Actions / ubuntu-latest，Python 3.12；被测约定 `http://127.0.0.1:8080` |
| 严重级别 | P1 |
| 状态 | 已确认 |
| 来源日志 | `samples/env_connection_refused.txt` |
| 工具分类 | `environment`（环境 / 基础设施） |
| 置信度 | 95% |
| 命中规则 | `env_connection_refused` |

## 现象

CI 中 `tests/test_posts_api.py::test_list_posts` 在 setup 阶段报错，整组接口冒烟无法执行，阻塞回归绿灯。

## 日志证据

```
ConnectionRefusedError: [Errno 111] Connection refused
requests.exceptions.ConnectionError: HTTPConnectionPool(host='127.0.0.1', port=8080):
Max retries exceeded with url: /posts
```

## 工具分类结果

- 类别：环境 / 基础设施
- 机器建议：检查被测服务是否启动、端口是否监听、CI 服务依赖是否就绪。
- 是否同意：**是**

## 人工结论

根因类型：**环境未就绪**

验证：同一 Runner 上 `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/posts` 得到 `000`；workflow 未启动 mock / 未配置 `services:`。  
不是断言写错——用例甚至没跑到 assert。

## 复现步骤

1. 不启动任何 API，仅跑 `pytest tests/test_posts_api.py::test_list_posts`
2. 观察 ERROR at setup
3. 期望：setup 前服务可连；实际：`Connection refused`

## 建议

- CI 增加 job 级 service 或 `docker compose up` 步骤，healthcheck 通过后再 `pytest`
- 本地 README 写明默认端口与启动命令
- 可选：conftest 在 session 开始做一次连通性探测，失败时跳过并给出明确 skip 原因（避免误报「用例失败」）

## 关联

- 用例：`tests/test_posts_api.py::test_list_posts`
- 报告：对 `samples/env_connection_refused.txt` 运行 CLI 生成的 `report.html`
