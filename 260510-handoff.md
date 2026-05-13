# Handoff — 2026-05-13

## 1. 当前状态

ChronoCare v0.4.0，main 分支，工作区干净。

## 2. 项目概况

- 路径: ~/dev/chronocare
- 技术栈: FastAPI + SQLAlchemy 2.0 + Alembic + HTMX + Tailwind + SQLite (WAL) + uv
- 功能路由: ~35 个 (页面 5 + API ~30)
- 模型: Person, Condition, BloodSugarRecord, Visit, MedicalRecord
- 页面入口: /dashboard, /persons, /blood-sugar, /visits, /medical-records

## 3. v0.4.0 变更 (2026-05-12)

### 后端增强 (T3)
- 清理已删除功能的残留路由引用
- 新增备份/恢复 API (POST /api/backup, POST /api/backup/restore, GET /api/backup/status)
- 4 个核心 API 端点支持分页+排序
- 创建 static 目录 + manifest.json

### 前端重做 (T4)
- base.html: GSAP 动画 + 响应式布局 + 深色模式 + PWA
- dashboard.html: Chart.js 血糖趋势 + 预警系统 + 人员切换
- 全套页面重写: persons / blood-sugar / visits / medical-records
- iPad/Mac 双端适配

### 数据库修复
- 修复 9 条乱码记录 (双重编码 UTF-8)
- scripts/fix_encoding.py 修复脚本

### 设计系统
- DESIGN.md 设计规范 (Google design.md spec)

## 4. 待处理事项

- [ ] OCR 实际服务集成 (当前 mock，推荐 PaddleOCR)
- [ ] DESIGN.md 设计落地 (字体/配色/图标)
- [ ] iPad 实机测试

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
| DESIGN.md | 设计系统规范 |
| vibe-coding-log/ | 按日期的开发日志 |
| src/chronocare/main.py | FastAPI 入口 |

## 7. 接手第一步

```bash
cd ~/dev/chronocare && git pull origin main
cat STATUS.md && cat DEV_PLAN.md
uv sync && uv run pytest
```
