# ChronoCare

老年父母健康管理平台 — v0.5.0

## 技术栈

- **后端**: FastAPI + SQLAlchemy 2.0 + Alembic
- **前端**: HTMX + Tailwind CSS + Jinja2 + Chart.js
- **数据库**: SQLite (WAL mode)
- **包管理**: uv

## 快速开始

```bash
# 安装依赖
uv sync

# 启动开发服务器
uv run uvicorn chronocare.main:app --reload

# 访问
open http://localhost:8000
```

## 项目结构

```
src/chronocare/
├── main.py          # FastAPI 入口
├── config.py        # 配置
├── database.py      # 数据库引擎
├── models/          # ORM 模型
├── schemas/         # Pydantic schemas
├── routers/         # API + 页面路由
├── services/        # 业务逻辑
├── templates/       # Jinja2 模板
└── static/          # 静态资源
```

## 开发

```bash
# 运行测试
uv run pytest

# Lint
uv run ruff check .
uv run ruff format .

# 类型检查
uv run mypy src/
```

## OCR 就医记录识别

ChronoCare 支持对就医记录、化验报告、处方、医嘱图片进行 OCR 文字识别，并通过 LLM 转换为结构化数据。

### 支持类型

| record_type | 描述 | 结构化字段 |
|---|---|---|
| `medical_record` | 就医记录 | diagnosis, symptoms, treatment, followup |
| `lab_report` | 化验报告 | tests: name/value/unit/reference/status |
| `prescription` | 处方 | medications: name/dosage/frequency/duration/notes |
| `doctor_order` | 医嘱 | medications, lifestyle, followup, special_instructions |

### 配置步骤

**1. 设置 OpenRouter API Key**

LLM 解析需要 OpenRouter API（支持 Google Gemini 等模型）：

```bash
# 方法1: 环境变量
export OPENROUTER_API_KEY=sk-or-v1-xxxx

# 方法2: .env 文件 (项目根目录)
echo "OPENROUTER_API_KEY=sk-or-v1-xxxx" >> .env
```

**2. 确保 Swift 可用（macOS OCR）**

文字识别使用 macOS Vision Framework，无需额外安装：

```bash
swift --version  # 确认 Swift 可用
```

**3. OCR 状态颜色说明**

化验结果表格中，状态列颜色含义：
- 🟢 **正常** (normal) — 绿色
- 🔴 **偏高/高** (high / slightly_high) — 红色
- 🟠 **偏低/低** (low / slightly_low) — 橙色

### API 端点

```
POST /api/medical-records/{id}/upload   # 上传图片
POST /api/medical-records/{id}/ocr      # 通用 OCR
POST /api/medical-records/{id}/process  # 自动识别（根据类型路由）
POST /api/medical-records/{id}/process-lab    # 识别化验单
POST /api/medical-records/{id}/process-order  # 识别医嘱/处方
```

### 错误处理

- 无图片: 返回 400 "No image uploaded"
- Swift 不可用: 返回 400 "OCR服务不可用"
- 无 API Key: OCR 文字仍会保存，结构化字段标记错误信息（不报 500）
