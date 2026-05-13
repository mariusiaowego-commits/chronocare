# Handoff — 2026-05-13

## 1. 当前状态

ChronoCare v0.5.0，main 分支干净，工作区无未提交改动。

## 2. 项目概况

- 路径: ~/dev/chronocare
- 技术栈: FastAPI + SQLAlchemy 2.0 + Alembic + HTMX + Tailwind + SQLite (WAL) + uv
- 功能路由: ~35 个 (页面 5 + API ~30)
- 模型: Person, Condition, BloodSugarRecord, Visit, MedicalRecord
- 页面入口: /dashboard, /persons, /blood-sugar, /visits, /medical-records

## 3. v0.5.0 变更 (2026-05-13)

### OCR 两层 Pipeline (核心新增)
- **Layer 1**: macOS Vision Framework
  - scripts/vision_ocr.swift — Swift OCR 脚本 (中英文)
  - src/chronocare/services/ocr_engine.py — Python subprocess 封装
- **Layer 2**: LLM 结构化解析
  - src/chronocare/services/ocr_parser.py — 4 种 prompt 模板
  - 配置: OPENROUTER_API_KEY + google/gemini-2.0-flash
- **集成**: services/medical_record.py — mock 全部替换为真实 pipeline
- **API**: POST /api/medical-records/{id}/process (自动路由)
- **前端**: detail.html 化验报告彩色状态 + 医嘱表格 + OCR 原始文本区
- **测试**: 27 个测试全部通过 (9 单元 + 16 集成 + 2 smoke)

### 文档更新
- STATUS.md / DEV_PLAN.md / README.md / AGENTS.md / wiki 全部更新为 v0.5.0
- pyproject.toml version → 0.5.0

## 4. 待处理事项

- [ ] 配置 OPENROUTER_API_KEY 到 .env (LLM 解析必需)
- [ ] 真图端到端验证 (上传化验单 → 结构化结果)
- [ ] iPad 实机测试响应式适配
- [ ] DESIGN.md 设计落地 (字体/配色/图标)
- [ ] 血糖趋势分析功能

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
| DESIGN.md | 设计系统规范 |
| vibe-coding-log/ | 按日期的开发日志 |
| scripts/vision_ocr.swift | macOS Vision OCR |
| src/chronocare/services/ocr_engine.py | Layer 1 封装 |
| src/chronocare/services/ocr_parser.py | Layer 2 LLM 解析 |
| src/chronocare/services/medical_record.py | 集成 (真实 pipeline) |

## 7. 接手第一步

```bash
cd ~/dev/chronocare && git pull origin main
cat STATUS.md && cat DEV_PLAN.md
uv sync && uv run pytest
# 配置 LLM API Key
echo "OPENROUTER_API_KEY=your_key" >> .env
```
