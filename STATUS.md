# ChronoCare STATUS

> 最后更新: 2026-05-14

## 当前阶段: v0.5.0 血糖趋势分析 + Hermes Skill

## 版本历史
| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-04 ~ 05-04 | Phase 1+2+3 完整功能 (147路由) |
| v0.3.0 | 2026-05-09 | 精简重构：删除40+文件，聚焦3核心功能 |
| v0.4.0 | 2026-05-12 | 前端重做 + 后端增强 + 响应式适配 |
| v0.5.0 | 2026-05-13 | OCR 两层 Pipeline — Swift Vision + LLM 解析 |

## 核心功能 (v0.5.0)

### 1. 人员档案管理 ✅
- Person + Condition 模型
- 父母双角色支持
- CRUD: API + 页面 (list/detail/form)

### 2. 血糖监控 ✅
- BloodSugarRecord 模型
- 空腹/餐后/睡前/随机 四种测量时机
- CRUD: API + 页面 (list/form)
- **趋势分析** (v0.5.0 新增):
  - 移动平均 (7天/14天)
  - 线性回归预测
  - TIR (Time in Range) 计算
  - CV (变异系数)
  - 智能预警 (连续高/低血糖)
  - Chart.js 可视化 (折线图 + 饼图)

### 3. 就诊记录 ✅
- Visit 模型
- 医院/科室/医生/诊断/处方
- CRUD: API + 页面 (list/form)

### 4. 就医记录 OCR ✅ (v0.5.0 真实实现)
- MedicalRecord 模型
- 支持4种类型: 就医记录/化验报告/处方/医嘱
- **Layer 1**: macOS Vision Framework (scripts/vision_ocr.swift)
- **Layer 2**: LLM 结构化解析 (services/ocr_parser.py, OpenRouter/Gemini)
- 化验报告彩色状态标记 (绿=正常, 红=偏高, 橙=偏低)
- 27 个测试全部通过

### 5. 仪表盘 ✅
- 人员切换器 + 健康预警横幅
- Chart.js 血糖趋势折线图 (近14天)
- GSAP 卡片入场动画 (stagger)
- 快捷操作 (血糖/就诊/OCR/记录)
- 深色模式 + 响应式 (iPad/Mac)

### 6. 数据备份 ✅
- 创建备份 / 恢复备份 / 备份状态
- API: POST /api/backup, POST /api/backup/restore, GET /api/backup/status

## v0.5.0 改动摘要

### 血糖趋势分析 (2026-05-14)
- src/chronocare/schemas/blood_sugar.py — 新增 BloodSugarTrend schema
- src/chronocare/services/blood_sugar.py — 新增 get_blood_sugar_trend(), get_blood_sugar_chart_data()
- src/chronocare/routers/api/blood_sugar.py — 新增 /api/blood-sugar/trend/{person_id}, /api/blood-sugar/chart-data/{person_id}
- src/chronocare/routers/pages/blood_sugar.py — 新增 /blood-sugar/trend 页面路由
- src/chronocare/templates/blood_sugar/trend.html — 趋势分析可视化模板
- src/chronocare/templates/base.html — 新增趋势分析导航链接

### Vision OCR 引擎 (2026-05-14)
- src/chronocare/services/vision_ocr.py — OpenRouter Vision API OCR 引擎 (跨平台)

### OCR Pipeline (T1-T4)
- scripts/vision_ocr.swift — macOS Vision OCR (中英文)
- src/chronocare/services/ocr_engine.py — Python subprocess 封装
- src/chronocare/services/ocr_parser.py — LLM 结构化解析 (4 种 prompt)
- src/chronocare/services/medical_record.py — mock 替换为真实 pipeline
- src/chronocare/routers/api/medical_record.py — 新增 /process 端点
- tests/services/test_ocr_parser.py — 9 个单元测试
- tests/test_services/test_medical_record.py — 16 个集成测试
- detail.html — 化验报告彩色状态 + 医嘱表格 + OCR 原始文本

## 路由统计
- 页面路由: 5 个 (/dashboard, /persons, /blood-sugar, /visits, /medical-records)
- API 路由: ~30 个 (含 CRUD + 备份 + OCR)
- 系统路由: /health, /docs, /openapi, /redoc

## Git
- 分支: main
- pyproject.toml version: 0.5.0
- 测试: 27/27 通过

## 开发命令
```bash
uv sync                                    # 安装依赖
uv run uvicorn chronocare.main:app --reload # 启动
uv run pytest                              # 测试
uv run ruff check .                        # Lint
uv run alembic upgrade head                # 数据库迁移
```
