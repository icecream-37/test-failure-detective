# 设计说明

## 要解决什么

CI / 本地 pytest 一红，值班要在「环境挂了、断言真失败、数据坏了、偶发 flaky」之间快速分流。  
纯贴日志或丢给通用 ChatBot，缺少**稳定、可回归、可抽检**的分类结果。

本工具：**规则优先**做离线分诊 → HTML/JSON 降噪 → **人工确认后写入 `findings/*.md`**。  
分类器是加速器；findings 才是测试交付物。

## 为何规则优先（而不是一上来 LLM）

| 点 | 说明 |
|----|------|
| 可演示、可 CI | 无 Key、无网络也能跑；pytest 能锁住行为 |
| 可解释 | 每条命中 `rule_id` + evidence，便于对照说明命中原因 |
| 误报可修 | 改 `rules.yaml` 即可迭代，不靠「再试一次 prompt」 |
| 成本 | 学生/小团队零推理费用 |

LLM 适合作为**第二遍**：对 `unknown` 或低置信度条目做摘要，但仍需人工落 findings。

## 架构

```
log.txt → 切分失败块 → rules.yaml 匹配（priority, confidence）
        → Finding[] → report.html / report.json
                    → 可选 --emit-finding-stub → findings/*.md 草稿
```

- **切分**：按 pytest `FAILURES` / `ERRORS` 与 `___ test ___` 头拆块  
- **匹配**：同块多规则时 `priority` 高者胜，其次 `confidence`  
- **扩展点**：`--rules` 换规则包；`accuracy.LABELED_SAMPLES` 做标注自检

## 误报怎么处理

1. 在对应 `findings` 里勾「纠正为…」，状态可「误报关闭」  
2. 补/收紧 `failure_detective/rules.yaml` 中的 pattern 或 priority  
3. 跑 `python -m failure_detective --self-check` 与 `pytest`，防止回归  

目标不是 100% 自动定根因，而是**先分对桶**，缩短打开完整日志的时间。

## 与兄弟项目的关系

[api-regression-jsonplaceholder](https://github.com/icecream-37/api-regression-jsonplaceholder) 负责「把接口测绿 + AI 用例评审」。  
本仓库负责「红了以后怎么分诊并归档」。典型链路：编写用例 → 跑 CI → 失败分诊 → 写入 findings。

## 可选后续（未实现）

- 第二遍 LLM hook：仅处理 `unknown`  
- 解析 JUnit XML / GitHub Actions annotation  
- 与 quarantine 列表联动，自动标 flaky 历史
