# [F-20261027-03] 结算按钮偶发不可点（重试后通过）

| 字段 | 内容 |
|------|------|
| 日期 | 2026-10-27 |
| 环境 | CI + pytest-rerunfailures / flaky 插件；并行 worker |
| 严重级别 | P3 |
| 状态 | 已确认 |
| 来源日志 | `samples/flaky_suspect.txt` |
| 工具分类 | `flaky_suspect`（疑似 Flaky） |
| 置信度 | 90% |
| 命中规则 | `flaky_keyword` |

## 现象

`test_checkout_button_enabled` 首次失败、rerun 通过；日志含 `ElementNotInteractable`、`time.sleep`、`passed on rerun`。

## 日志证据

```
Rerun attempt 1 of 2 failed; passed on rerun.
time.sleep(0.3)
ElementNotInteractableException: element not interactable
Hint: timing issue — button enabled only after price API returns
FLAKY ... passed on rerun
```

## 工具分类结果

- 类别：疑似 Flaky
- 机器建议：标记 quarantine、查重试历史，再查竞态或共享状态。
- 是否同意：**是**

## 人工结论

根因类型：**Flaky（时序 / 竞态）**

验证：连续单线程重跑 10 次失败 2 次；去掉 `sleep` 改为等待 `#checkout[data-ready=true]` 后 10 次全过。  
结论：不是业务功能必现缺陷，是等待策略不当；需修用例，而不是先改产品。

## 复现步骤

1. 并行跑 UI checkout 相关用例
2. 观察首次失败 + rerun pass
3. 期望：稳定绿；实际：间歇红

## 建议

- 用显式等待替换 `sleep`
- 短期 `@pytest.mark.flaky` 或 quarantine 并建技术债单
- 在分诊报告中优先把 flaky 与「真断言失败」分开，避免值班噪音

## 关联

- 用例：`tests/test_ui_checkout.py::test_checkout_button_enabled`
- 报告：`samples/flaky_suspect.txt` → CLI
