# Handoff — 2026-05-15

## 1. 当前状态

ChronoCare v0.5.0，main 分支，工作区干净。4 条 commits 待 push 到 origin/main。

## 2. 项目概况

- 路径: ~/dev/chronocare
- 技术栈: FastAPI + SQLAlchemy 2.0 + Alembic + HTMX + Tailwind + SQLite (WAL) + uv
- 模型: Person, Condition, BloodSugarRecord, Visit, MedicalRecord
- 页面入口: /dashboard, /persons, /blood-sugar, /visits, /medical-records
- 测试: 27/27 通过

## 3. v0.5.0 完整变更 (2026-05-13 ~ 05-14)

### OCR 两层 Pipeline
- **Layer 1**: macOS Vision Framework (scripts/vision_ocr.swift)
- **Layer 2**: LLM 结构化解析 (services/ocr_parser.py, OpenRouter/Gemini)
- **集成**: services/medical_record.py — mock 全部替换为真实 pipeline
- **API**: POST /api/medical-records/{id}/process (自动路由)
- **前端**: detail.html 化验报告彩色状态 + 医嘱表格 + OCR 原始文本区

### 血糖趋势分析 (05-14 新增)
- services/blood_sugar.py — get_blood_sugar_trend(), get_blood_sugar_chart_data()
- routers/api/blood_sugar.py — /api/blood-sugar/trend/{person_id}, /api/blood-sugar/chart-data/{person_id}
- routers/pages/blood_sugar.py — /blood-sugar/trend 页面路由
- templates/blood_sugar/trend.html — Chart.js 可视化 (折线图 + 饼图)
- 功能: 移动平均(7天/14天) / 线性回归预测 / TIR / CV / 智能预警

### vision_ocr.py 已删除
- 原 services/vision_ocr.py (OpenRouter Vision API) 已移除
- OCR 改由 hermes skill 方案处理，不嵌入应用代码

### 文档状态
- STATUS.md — 更新至 05-14，包含趋势分析说明 ✅
- DEV_PLAN.md — 更新至 05-13，Phase 6 待规划 ⚠️
- pyproject.toml version: 0.5.0

## 4. 待处理事项

- [ ] **push 4 条 commits 到 origin/main** (e2f362a 等)
- [ ] 配置 OPENROUTER_API_KEY 到 .env (LLM 解析必需)
- [ ] 真图端到端验证 (上传化验单 → 结构化结果)
- [ ] iPad 实机测试响应式适配
- [ ] DESIGN.md 设计落地 (字体/配色/图标)
- [ ] DEV_PLAN.md 更新 — 血糖趋势已完成，规划下一步功能

## 5. 开发规范

- worktree 工作流: main=稳定，开发用 worktree，PR feature→main
- PR 流程: 改代码→本地测试→报结果→用户确认→提PR
- 未测不提 PR
- Lint: ruff (B008全局忽略, E501 per-file)
- 测试: pytest (27 tests)
- GitHub: HTTPS + `gh auth setup-git` 认证 (SSH 有 SOCKS proxy 干扰)

## 6. 关键文件

| 文件 | 用途 |
|------|------|
| STATUS.md | 项目状态总览 |
| DEV_PLAN.md | 开发计划与进度 |
| AGENTS.md | Agent 开发规范 |
| scripts/vision_ocr.swift | macOS Vision OCR |
| src/chronocare/services/ocr_engine.py | Layer 1 封装 |
| src/chronocare/services/ocr_parser.py | Layer 2 LLM 解析 |
| src/chronocare/services/medical_record.py | OCR 集成 |
| src/chronocare/services/blood_sugar.py | 血糖 CRUD + 趋势分析 |
| templates/blood_sugar/trend.html | 趋势分析可视化 |

## 7. 接手第一步

```bash
cd ~/dev/chronocare && git pull origin main
cat STATUS.md && cat DEV_PLAN.md
uv sync && uv run pytest
echo "OPENROUTER_API_KEY=your_key" >> .env
```
