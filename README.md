# ChronoCare

老年父母健康管理平台

## 技术栈

- **后端**: FastAPI
- **前端**: HTMX + Jinja2 模板
- **数据库**: SQLite
- **样式**: 待定 (可选 Tailwind CSS 或自定义 CSS)

## 项目结构

```
chronocare/
├── app/                    # 主应用目录
│   ├── routers/           # 路由处理
│   ├── models/            # 数据模型
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # 业务逻辑
│   └── main.py           # FastAPI 入口
├── templates/             # HTMX/Jinja2 模板
├── static/                # 静态资源
│   ├── css/
│   ├── js/
│   └── img/
├── data/                  # SQLite 数据库文件
├── tests/                 # 测试
├── requirements.txt       # 依赖
└── README.md
```

## 快速开始

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # macOS/Linux

# 安装依赖
pip install -r requirements.txt

# 运行应用
uvicorn app.main:app --reload
```

访问 http://localhost:8000

## 功能规划

- [ ] 用户管理（家庭成员）
- [ ] 健康数据记录
- [ ] 用药提醒
- [ ] 就诊记录
- [ ] 健康报告生成