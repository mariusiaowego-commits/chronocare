# Handoff — 2026-05-10

## 1. 当前状态

ChronoCare v0.3.0 稳定版，main 分支干净，无未提交改动。

## 2. 项目概况

- 路径: ~/dev/chronocare
- 技术栈: FastAPI + SQLAlchemy 2.0 + Alembic + HTMX + Tailwind + SQLite (WAL) + uv
- 功能路由: ~47 个
- 模型: Person, Condition, BloodSugarRecord, Visit, MedicalRecord
- 页面入口: /persons, /blood-sugar, /visits, /medical-records

## 3. v0.3.0 变更 (2026-05-09)

精简重构：从147路由砍到47路由，删除40+文件。
保留3核心功能 + 1新增功能：
- ✅ 人员档案管理 (Person + Condition)
- ✅ 血糖监控 (BloodSugarRecord)
- ✅ 就诊记录 (Visit)
- ✅ 就医记录 OCR (MedicalRecord，OCR为mock占位)

已移除: 血压记录、用药管理、仪表盘、知识库、健康新闻、
统计报表、趋势预警、周报/月报、邮件通知、血糖波动分析、
血压昼夜节律、用药依从性、PDF导出、数据备份/恢复、
用药提醒、健康档案汇总

## 4. 待处理事项

- OCR 实际服务集成 (当前mock，需选型)
- Phase 4 方向待确认 (DEV_PLAN.md)
- pyproject.toml version 仍为 0.1.0，建议更新为 0.3.0
- 血压相关功能已移除，Phase 4 血压变异性分析需确认是否保留

## 5. 开发规范

- worktree 工作流: main=稳定，开发用 worktree，PR feature→main
- PR 流程: 改代码→本地测试→报结果→用户确认→提PR
- 未测不提 PR
- Lint: ruff (B008全局忽略, E501 per-file)
- 测试: pytest

## 6. 关键文件

| 文件 | 用途 |
|------|------|
| STATUS.md | 项目状态总览 |
| DEV_PLAN.md | 开发计划与进度 |
| AGENTS.md | Agent 开发规范 |
| vibe-coding-log/ | 按日期的开发日志 |
| src/chronocare/main.py | FastAPI 入口 |

## 7. 接手第一步

```bash
cd ~/dev/chronocare && git pull origin main
cat STATUS.md && cat DEV_PLAN.md
uv sync && uv run pytest
```
