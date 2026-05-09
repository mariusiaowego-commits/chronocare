# chronocare AGENTS

老年父母健康管理平台 — 精简版，专注核心功能。

## 项目路径
`/Users/mt16/dev/chronocare`

## 技术栈
- **后端**: FastAPI + SQLAlchemy 2.0 + Alembic
- **前端**: HTMX + Tailwind CSS + Jinja2
- **数据库**: SQLite (WAL mode)
- **包管理**: uv

## 核心功能 (v0.3.0)

### 1. 人员档案管理
- Person + Condition 模型
- 父母双角色支持

### 2. 血糖监控
- 母亲糖尿病日常管理
- 血糖记录 CRUD (空腹/餐后/睡前/随机)
- 自动预警 (高/低血糖)

### 3. 就诊记录
- 双角色就诊时间记录
- 医院/科室/医生/诊断/处方

### 4. 就医记录OCR (新增)
- 图片上传 + OCR识别
- 医嘱结构化存储
- 化验单OCR → 结构化结果
- 支持4种类型: 就医记录/化验报告/处方/医嘱

## 项目结构
```
src/chronocare/
├── main.py                    # FastAPI 入口
├── config.py                  # 配置
├── database.py                # 数据库引擎
├── models/
│   ├── base.py                # Base 模型
│   ├── person.py              # Person + Condition
│   ├── blood_sugar.py         # BloodSugarRecord
│   ├── visit.py               # Visit
│   └── medical_record.py      # MedicalRecord (新增)
├── schemas/
│   ├── person.py
│   ├── blood_sugar.py
│   ├── visit.py
│   └── medical_record.py      # 新增
├── routers/
│   ├── api/
│   │   ├── person.py
│   │   ├── blood_sugar.py
│   │   ├── visit.py
│   │   └── medical_record.py  # 新增
│   └── pages/
│       ├── person.py
│       ├── blood_sugar.py
│       ├── visit.py
│       └── medical_record.py  # 新增
├── services/
│   ├── person.py
│   ├── blood_sugar.py
│   ├── visit.py
│   └── medical_record.py      # 新增 (含OCR占位)
├── templates/
│   ├── base.html
│   ├── person/
│   ├── blood_sugar/
│   ├── visit/
│   └── medical_record/        # 新增
│       ├── list.html
│       ├── form.html
│       └── detail.html
└── static/
```

## 页面入口
```
/                    → /persons (重定向)
/persons             → 人员列表
/blood-sugar         → 血糖记录
/visits              → 就诊记录
/medical-records     → 就医记录OCR
```

## API 端点
```
GET/POST   /api/persons
GET/POST   /api/blood-sugar
GET/POST   /api/visits
GET/POST   /api/medical-records
POST       /api/medical-records/{id}/upload    # 上传图片
POST       /api/medical-records/{id}/ocr       # 通用OCR
POST       /api/medical-records/{id}/process-lab   # 化验单识别
POST       /api/medical-records/{id}/process-order # 医嘱识别
```

## 开发命令
```bash
uv sync                  # 安装依赖
uv run uvicorn chronocare.main:app --reload   # 启动
uv run pytest            # 测试
uv run ruff check .      # Lint
uv run alembic upgrade head  # 数据库迁移
```

## 数据库迁移
```bash
uv run alembic revision --autogenerate -m "描述"
uv run alembic upgrade head
```

## 当前进度
- Phase 1 MVP ✅
- Phase 2 增强功能 ✅
- Phase 3 周报/月报 PDF 导出 ✅
- Phase 4 精简重构 (v0.3.0) ✅
  - 删除40+文件，保留3核心功能
  - 新增就医记录OCR功能

## OCR 实现状态
当前为占位实现 (mock)，需要集成实际OCR服务:
- PaddleOCR (推荐，中文识别优秀)
- Tesseract (开源，需安装)
- 云API (百度/腾讯/阿里云)

## 注意
- GitHub push/pull 用 HTTPS URL
- 有 DEV_PLAN.md / STATUS.md 追踪进度
- 数据库文件: chronocare.db (SQLite)

## 收尾文档
- STATUS.md — 项目根目录
- DEV_PLAN.md — 项目根目录
- vibe-coding-log/ — 项目根目录，按日期记录
- wiki — `hermes-base/projects/project-chronocare.md`
