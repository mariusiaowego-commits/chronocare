# ChronoCare STATUS

> 最后更新: 2026-05-20

## 当前阶段: v0.5.0 + 前端重设计 + 表单校验 + UX 优化

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

## Git
- 分支: main
- 最新 commit: ba44ce3
- pyproject.toml version: 0.5.0
- 测试: 41/41 通过

## 开发命令
```bash
uv sync                                    # 安装依赖
uv run uvicorn chronocare.main:app --reload # 启动
uv run pytest                              # 测试
uv run ruff check .                        # Lint
uv run alembic upgrade head                # 数据库迁移
```
