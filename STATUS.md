# ChronoCare STATUS

> 最后更新: 2026-06-11

## 当前阶段: v0.7.0 — 健康报告生成体验升级

## 版本历史
| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-04 ~ 05-04 | Phase 1+2+3 完整功能 (147路由) |
| v0.3.0 | 2026-05-09 | 精简重构：删除40+文件，聚焦3核心功能 |
| v0.4.0 | 2026-05-12 | 前端重做 + 后端增强 + 响应式适配 |
| v0.5.0 | 2026-05-13 | OCR 两层 Pipeline — Swift Vision + LLM 解析 |
| v0.6.0 | 2026-06-11 | 测试隔离 + 生产 DB 清理 (123 person + 80 medical_records) |
| v0.7.0 | 2026-06-11 | 健康报告生成体验全面升级 (PR #6) |

## 核心功能 (v0.5.0)

### 1. 人员档案管理 ✅
- Person + Condition 模型
- 父母双角色支持
- CRUD: API + 页面 (list/detail/form)
- **blur 实时校验** (2026-05-20): 姓名/出生日期/身高/体重
- **女性角色深粉红卡片** (2026-05-20): Dashboard + 列表 + 详情

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
- **图片预览 + Lightbox** (2026-05-20): 点击放大查看原件
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

### 7. Lucide Icon 系统 ✅ (2026-05-20 新增)
- 28 个 Lucide Outline SVG icon
- Jinja2 macro (`macros/icon.html`) 统一调用
- 0 emoji 残留，全部替换为 SVG
- 深色模式 `currentColor` 自动适配

## 2026-05-20 改动摘要

### Lucide Icon 重设计
- 删除全部 46 处 emoji，替换为 28 个 Lucide Outline SVG
- 新增 `templates/icons/` (28 SVG) + `templates/macros/icon.html`
- 后端 `alert.icon` 字段从 emoji 改为 Lucide 名称字符串
- 设计文档: `docs/icon-redesign-prd.md`

### 表单校验
- 前端 blur 实时校验 (姓名/出生日期/身高/体重)
- 后端 ValidationError 捕获 + 错误回显 + 数据回填
- 编辑档案同样受保护

### UX 修复
- 移动端抽屉不响应: 移除冲突的 `transform` class + resize 监听
- 图片预览: `/uploads` 静态挂载 + `<img>` + Lightbox
- 女性角色深粉红: Dashboard 渐变 + 列表边框 + 详情图标

## 2026-06-11 改动摘要

### 测试隔离 (v0.6.0)
- `tests/conftest.py` 重写：session-scoped monkeypatch `_isolated_engine` fixture
- SQLite `.backup()` 从生产 DB 拷贝到 tmp 目录，swap engine + session_factory
- 生产 `database.py` 零改动，uvicorn :8000 不受影响
- 测试后生产 DB 零污染（已验证两次 run）
- 分支: `feat/test-isolation` (commit 3989999)

### 生产 DB 清理
- 一次性脚本 `scripts/cleanup_test_pollution.py` 已执行
- 删除: 123 person + 80 medical_records (历史测试污染)
- 备份: `data/backups/chronocare-pre-cleanup-20260611-085928.db`
- 清理后: 2 真实 person (qian, tjh) + 66 真实 medical_records

### Alma agent 调研 (2026-06-10, default profile)
- commit bc886ce: PRD + 调研报告 (纯文档，未动业务代码)

### 健康报告体验升级 (v0.7.0, PR #6)
- Preflight 环境检查: hermes CLI / Nous Portal / FAL / chat 模型验证
- 超时重试: _hermes_image_generate 自动重试 2 次
- 图片本地保存: data/reports/ 目录
- Dashboard 报告画廊: 缩略图 + 全屏预览 + 失败原因展示
- Prompt 重写: v3 详细结构 (6站点/4 bento卡片/对比表/行动便签)
- 诊断归一化: 二尖瓣/心房颤动/高血压 变体处理
- 生图超时: 120s → 300s

## 2026-06-09 改动摘要

### 云胶片影像查看器
- 新增 `/cloud-films` 路由，按 DICOM series 分类展示 CT 影像
- 10 个影像序列：定位像、心脏薄层、增强薄层、AI 分析等（共 1377/1512 张）
- 全屏查看模式：键盘左右切换、Escape 退出
- sidebar 导航集成，深色模式支持
- XHR 拦截 + UID 映射下载方案（绕过 Playwright UTF-8 charset 解码损坏）
- 分支: `main` (commit 973136a)

### AGENTS.md 优化
- 融合 dizical 项目的 git/GitHub 工作流习惯
- 新增：feature branch → PR（未测不推）
- 新增：HTTPS push fallback 配置
- 新增：收尾 Checklist（9 项）

## 2026-06-08 改动摘要

### tjh 就诊记录批量导入
- 49 个 PDF (2024-03-13 ~ 2026-05-27) → 49 MedicalRecord + 41 Visit (person_id=2)
- 解析策略: pdftotext + 正则; 修复 `诊 断` 正则会误抓现病史段的 bug
- `VisitRead.attachments` schema 修复: `dict` → `list[str]` (解决 /api/visits 500)
- 新增 `scripts/import_tjh_pdfs.py` (--dry-run / 真实导入 / --rollback 三模式)
- DB 备份: `data/backups/chronocare-pre-tjh-import-20260608-171018.db`
- 分支: `feature/tjh-import-49-pdfs` (从 main @ 5a93976)
- 端口: 8000 = chronocare (现有 --reload 长跑), 不要启新进程
- 详情: `260608-handoff.md` + `vibe-coding-log/2026-06-08.md`

## 2026-05-25 改动摘要

### 数据清理
- 删除 medical_records id=114 (重复测试残留)
- 删除 30 条 "测试人员" persons + 32 条孤儿 medical_records
- 保留 21 条血糖记录 (待确认是否真实数据)

### 代码质量
- ruff 零警告: test_normalize.py (I001 + F541)

### OCR 管线验证
- vision_analyze 识别真实化验单: 22 项，status 判断正确
- 规范化层 + 页面渲染均正常，管线无退化

## 2026-06-09 改动摘要

### 健康报告图 Feature (PR #4 ✅ merged)
- `feat/health-report` → PR #4 → merged to main @ e54df9b
- T1: ReportGeneration model + data aggregation + API
- T3: Hermes CLI subprocess image_generate + baoyu prompt
- T6: 前端 modal + 历史列表 + dashboard 入口
- Bug fix: extract_doctor 正则双重转义 (中文匹配失败)
- 测试: 67/67 通过 (含 26 个新测试)
- 数据清理: 177 条测试残留已删除

## Git
- 当前分支: `main` @ a9a2249 (PR #6 merged)
- 工作流: feature branch → commit → PR（不用 worktree）
- pyproject.toml version: 0.6.0
- 测试: 67/67 通过（隔离 engine，零生产污染）

## 开发命令
```bash
uv sync                                    # 安装依赖
uv run uvicorn chronocare.main:app --reload # 启动
uv run pytest                              # 测试
uv run ruff check .                        # Lint
uv run alembic upgrade head                # 数据库迁移
```
