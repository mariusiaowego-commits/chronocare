# ChronoCare

老年父母健康管理平台

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
