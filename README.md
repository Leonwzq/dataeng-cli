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
