# Data Engineering CLI Demo (科研公共数据源采集与集成)

一个专注于科研公共数据资产采集、增量同步（Watermark）、幂等去重以及结构化数据质量校验的 Python 命令行工具。

## 📌 项目简介
本工具示范了如何将分散在 UniProt（蛋白数据库）等公共 API 中的数据，规范化提取至本地可信资产库。系统设计了异常退避重试、SQLite 游标状态管理、自动日期格式修正、质量报告生成与 Mock 离线演示模式。

## 🛠️ 技术选型
- **语言/运行时**: Python 3.10+
- **CLI 框架**: `click` + `rich` (高可读终端提示)
- **网络与 Schema 校验**: `requests` + `pydantic`
- **状态持久化 (Watermark & 去重)**: SQLite3 (零外部依赖数据库)
- **任务调度**: `schedule`

## ⚙️ 环境变量配置方式
系统支持通过环境变量控制配置（如超时设置或日志级别）：
```bash
export DATAENG_TIMEOUT=15
export DATAENG_LOG_LEVEL=DEBUG
——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
安装使用过程演示：
本地源码安装
# 1. 克隆项目并进入目录
git clone https://github.com/Leonwzq/dataeng-cli.git
cd dataeng-cli

# 2. 以可编辑模式安装 CLI
python3 -m pip install .
echo 'export PATH="$HOME/Library/Python/3.9/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
CLI 命令说明
1. 原始数据采集 (fetch)
支持按关键词拉取 UniProt 原始 JSON 格式响应，包含重试与错误提示。

# 真实网络请求
dataeng-cli fetch --source uniprot --query "insulin" --output ./data/raw

# 离线/Mock 演示模式
dataeng-cli fetch --source uniprot --query "insulin" --mock
输出结果:
 INFO  正在请求 UniProt API (尝试 1/3): query=insulin
✓ 采集成功！原始响应保存在: data/raw/uniprot_insulin.json
2. 增量同步与去重 (sync)
维护 SQLite 本地水位线 (Watermark)，提取新增或变更数据，并自动完成日期格式归一化清洗。

# 指定水位线增量拉取
dataeng-cli sync --source uniprot --since 2026-07-01

# 定时调度模式演示 (每 5 秒自动触发一次)
dataeng-cli sync --source uniprot --mock --schedule-mode
输出结果:
开始同步 [uniprot] 数据，当前 Watermark: 2026-07-01
同步完成！新增: 5 | 更新: 0 | 跳过(幂等去重): 0
3. 数据质量校验 (validate)
校验处理后数据的完整率、重复率以及 Schema 符合性，输出结构化报告，并支持存盘。

# 运行校验并保存报告至 result.json
dataeng-cli validate ./data/processed --format json --output result.json
JSON 结构化输出结果:

{
  "total_records": 5,
  "completeness_rate": 1.0,
  "duplicate_rate": 0.0,
  "schema_errors": 0,
  "stale_records": 0,
  "pass": true,
  "comment": "数据质量校验通过。"
}
已实现功能
1. 数据采集：支持按查询拉取 UniProt 原始数据，带 3 次指数退避重试，原始 API 响应完整落盘。
2. 增量与去重：使用 SQLite 记录 primaryAccession 及最后修改时间，重复运行不产生重复数据（满足幂等性）。
3. 数据清洗：支持自动修复 ISO/标准日期格式归一化。
4. 质量校验：对必填项完整率、重复率、字段类型做自动化评估，并输出可配置的 JSON 报告。
5. Mock 与测试：全流程提供 --mock 参数，无需网络即可完整演示采集-同步-校验全链路。
6. 任务调度：提供 --schedule-mode 实现简易定时轮询同步。
