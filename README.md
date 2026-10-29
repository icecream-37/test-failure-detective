# Test Failure Detective（失败日志侦探）

> 吃 pytest / CI 失败日志 → 分成 **环境 / 断言 / 测试数据 / 疑似 Flaky** → 出 HTML + JSON → **人工确认后写入 `findings/*.md`**  
> 面向测试团队排障降噪，不是通用 ChatBot 套壳。

与兄弟项目 [api-regression-jsonplaceholder](https://github.com/icecream-37/api-regression-jsonplaceholder) 互补：那边把接口回归跑绿；这边处理「红了以后怎么分诊并归档」。

## 解决什么问题

| 痛点 | 本工具 |
|------|--------|
| 一红就翻很长 log | 按失败块分诊 + 证据片段 |
| 环境问题被当成用例烂 | `environment` 桶优先提示查服务/依赖 |
| 只有口头结论 | `findings/` 模板把确认结果写成可跟踪记录 |
| 黑盒结论难追溯 | 规则 `rule_id` 可解释，可 `--self-check` |

## 快速开始

```bash
cd test-failure-detective
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 自测（分类器本身）
pytest -q

# 演示：对样例日志出报告
python -m failure_detective samples/env_connection_refused.txt --out out/
# 打开 out/report.html

# 标注样本准确率自检
python -m failure_detective --self-check

# 分类 + 生成 findings 草稿
python -m failure_detective samples/mixed_ci_log.txt --out out/ \
  --emit-finding-stub --findings-dir out/findings-stubs
```

也可：`pip install -e .` 后使用入口命令 `failure_detective ...`。

## 分类说明

| 类别 | 含义 | 典型信号 |
|------|------|----------|
| `environment` | 环境 / 基础设施 | Connection refused、DNS、超时、5xx、ModuleNotFound、权限 |
| `assertion` | 断言失败 | AssertionError、expected vs actual |
| `test_data` | 测试数据 / Fixture | KeyError/IndexError、fixture 错误、非法 JSON 夹具 |
| `flaky_suspect` | 疑似不稳定 | flaky、passed on rerun、竞态/sleep/显式等待超时 |
| `unknown` | 未命中规则 | 需人工看全文，或补规则 |

规则配置：`failure_detective/rules.yaml`（可用 `--rules` 覆盖）。

## 核心工作流（测试产出在 findings）

```
跑侦探 → 看 HTML → 人工确认 → 写入 findings/*.md
```

1. CLI 生成 `report.html` / `report.json`（机器分诊，**不能**直接当缺陷结论）  
2. 打开报告，按「环境 > 数据 > 断言 > flaky」处理  
3. 对确认的问题：用 [`findings/FINDING_TEMPLATE.md`](findings/FINDING_TEMPLATE.md)，或 `--emit-finding-stub`  
4. 填「人工结论 / 复现 / 建议」，更新状态  

示例归档：

- [`findings/F-20261027-01_posts-api-connection.md`](findings/F-20261027-01_posts-api-connection.md) — 环境  
- [`findings/F-20261027-02_user-email-assertion.md`](findings/F-20261027-02_user-email-assertion.md) — 断言  
- [`findings/F-20261027-03_checkout-flaky.md`](findings/F-20261027-03_checkout-flaky.md) — Flaky  

详见 [`findings/README.md`](findings/README.md)。

## 准确率自检

1. 维护少量**已标注**样例（`samples/` + `failure_detective/accuracy.py`）  
2. `python -m failure_detective --self-check` 查看命中率  
3. 误报：在 finding 里纠正分类，并改 `rules.yaml`，再跑 `pytest` 防回归  

工具负责初筛与降噪；**人工抽检与 findings 归档**才是最终结论——采纳或纠正都会留在 `findings/` 中。

## 限制

- 默认是**规则引擎**，不是大模型；复杂语义可能进 `unknown`  
- 日志格式偏 pytest；其它格式可能要改切分或规则  
- 分类 ≠ 根因最终结论；必须以人工 findings 为准  
- 后续可对 `unknown` 接 LLM 第二遍（设计见 [`docs/design.md`](docs/design.md)）

## 目录结构

```
failure_detective/     # 包：分类、报告、CLI、规则 YAML
samples/               # 演示用失败日志
tests/                 # 分类器自测
findings/              # 模板 + 示例发现（测试产出）
docs/design.md
```

## 许可证

MIT
