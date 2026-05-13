# ChronoCare STATUS

> 最后更新: 2026-05-13

## 当前阶段: v0.4.0 前端重做完成

## 版本历史
| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-04 ~ 05-04 | Phase 1+2+3 完整功能 (147路由) |
| v0.3.0 | 2026-05-09 | 精简重构：删除40+文件，聚焦3核心功能 |
| v0.4.0 | 2026-05-12 | 前端重做 + 后端增强 + 响应式适配 |

## 核心功能 (v0.4.0)

### 1. 人员档案管理 ✅
- Person + Condition 模型
- 父母双角色支持
- CRUD: API + 页面 (list/detail/form)

### 2. 血糖监控 ✅
- BloodSugarRecord 模型
- 空腹/餐后/睡前/随机 四种测量时机
- CRUD: API + 页面 (list/form)

### 3. 就诊记录 ✅
- Visit 模型
- 医院/科室/医生/诊断/处方
- CRUD: API + 页面 (list/form)

### 4. 就医记录 OCR ✅ (模型+路由就绪，OCR为占位实现)
- MedicalRecord 模型
- 支持4种类型: 就医记录/化验报告/处方/医嘱
- 图片上传 + OCR处理接口 (mock，待集成实际OCR服务)
- CRUD: API + 页面 (list/detail/form)

### 5. 仪表盘 ✅ (v0.4.0 新增)
- 人员切换器 + 健康预警横幅
- Chart.js 血糖趋势折线图 (近14天)
- GSAP 卡片入场动画 (stagger)
- 快捷操作 (血糖/就诊/OCR/记录)
- 深色模式 + 响应式 (iPad/Mac)

### 6. 数据备份 ✅ (v0.4.0 新增)
- 创建备份 / 恢复备份 / 备份状态
- API: POST /api/backup, POST /api/backup/restore, GET /api/backup/status

## v0.4.0 改动摘要

### 后端增强 (T3)
- 清理已删除功能的残留路由引用
- 新增备份/恢复 API
- 4 个核心 API 端点支持分页+排序
- 创建 static 目录

### 前端重做 (T4)
- base.html: GSAP 动画 + 响应式布局 + 深色模式 + PWA manifest
- dashboard.html: Chart.js 血糖趋势 + 预警系统 + 人员切换
- 全套页面重写: persons / blood-sugar / visits / medical-records
- iPad/Mac 双端适配

### Bug 修复
- dashboard.html 重复 endblock 导致 500 错误
- ruff lint 清理 (import sorting, unused variables)

## 路由统计
- 页面路由: 5 个 (/dashboard, /persons, /blood-sugar, /visits, /medical-records)
- API 路由: ~30 个 (含 CRUD + 备份 + OCR)
- 系统路由: /health, /docs, /openapi, /redoc

## 已删除功能 (v0.3.0 精简)
血压记录、用药管理、知识库、健康新闻、
统计报表、趋势预警、周报/月报、邮件通知、
血糖波动分析、血压昼夜节律、用药依从性、PDF导出、
用药提醒、健康档案汇总

## 待完成
- [ ] OCR 实际服务集成 (PaddleOCR/云API，待选型)
- [ ] 多端适配测试 (iPad 实机验证)
- [ ] 本地打包 (.app)

## Git
- 分支: main
- 工作区: 有待提交改动 (见 git status)
- 最新提交: 8ea1249 merge: T4 前端重写
- pyproject.toml version: 0.4.0

## 开发命令
```bash
uv sync                                    # 安装依赖
uv run uvicorn chronocare.main:app --reload # 启动
uv run pytest                              # 测试
uv run ruff check .                        # Lint
uv run alembic upgrade head                # 数据库迁移
```
