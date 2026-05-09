# chronocare AGENTS

老年父母健康管理平台。

## 项目路径
`/Users/mt16/dev/chronocare`

## 技术栈
- **后端**: FastAPI + SQLAlchemy 2.0 + Alembic
- **前端**: HTMX + Tailwind CSS + Jinja2 + Chart.js
- **数据库**: SQLite (WAL mode)
- **包管理**: uv

## 核心功能
- 健康档案管理（老人信息）
- 血糖记录 CRUD
- 血压记录 CRUD
- 用药管理 CRUD
- 就诊记录 CRUD
- 统计报表（血糖分布饼图/血压分级/周对比）
- 趋势预警（自动检测异常健康模式）
- 周报/月报 PDF 导出
- 用药提醒 + 邮件通知
- 健康档案汇总页（健康评分 0-100）

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

## 开发命令
```bash
uv sync                  # 安装依赖
uv run uvicorn chronocare.main:app --reload   # 启动
uv run pytest            # 测试
uv run ruff check .      # Lint
```

## 当前进度
- Phase 1 MVP ✅
- Phase 2 增强功能（统计报表/预警/健康档案）✅
- Phase 3 周报/月报 PDF 导出 ✅

## 注意
- GitHub push/pull 必须用 HTTPS URL
- 有 DEV_PLAN.md / STATUS.md 追踪进度

## 收尾文档
- STATUS.md — 项目根目录
- DEV_PLAN.md — 项目根目录（注意不是 DEVELOPMENT_PLAN.md）
- vibe coding log — **无**
- wiki — **无**（未建立）
