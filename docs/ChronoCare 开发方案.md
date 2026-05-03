# ChronoCare — 老年健康管理平台开发方案

> 版本: v0.1 (Planning)
> 编制日期: 2026-05-02
> 编制人: Coder Agent (Hermes)
> 项目路径: ~/dev/chronocare
> Obsidian: tqob/05 Coding/project-chronocare

---

## 1. 项目概述

**定位**: 一个面向中年子女的老年父母健康管理平台，用于系统化管理老人的日常医疗数据、用药记录、就诊历史，并构建持续积累的医疗知识库。

**目标用户**: 用户本人（管理母亲和父亲两位老人的健康数据）

**核心价值**:
- 将分散的医疗信息集中管理，不再依赖记忆和零散笔记
- 血糖/血压异常实时预警，不错过关键指标变化
- 持续积累医疗知识，形成家庭健康知识库
- 就诊/复诊/配药全记录，就医时有据可查

**母亲侧重点**:
- 2型糖尿病 + 高血压 → 血糖监控、血压监测、饮食管理
- 皮肤科（手部湿疹/皮屑） → 症状记录、护肤知识
- 复诊/配药习惯管理

**父亲侧重点**:
- 心脏问题 + 二尖瓣脱垂 → 血压/心率监测、心脏健康知识
- 失眠 + 安眠药 → 睡眠记录、用药管理
- 心梗预防 + 防猝死 → 预警规则、急救知识

---

## 2. 技术架构

### 2.1 技术栈

| 层 | 选型 | 理由 |
|----|------|------|
| Web 框架 | FastAPI | Python 生态最佳 ASGI 框架，自带 OpenAPI |
| 模板引擎 | Jinja2 | 服务端渲染，首屏快，SEO 友好 |
| 动态交互 | HTMX | 无需 JS 构建，局部更新，代码量极少 |
| CSS | Tailwind CSS | 实用优先，暗色模式内置，移动端友好 |
| ORM | SQLAlchemy 2.0 | 成熟稳定，抽象层可切换数据库 |
| 数据库 | SQLite (WAL) | 零运维，单文件易备份，数据量小完全够用 |
| 数据库迁移 | Alembic | 版本管理表结构变更 |
| 包管理 | uv | Rust 实现，超快，PEP 621 兼容 |
| 图表 | Chart.js | 轻量，折线图/柱状图/饼图齐全 |
| Lint | ruff | 替代 black+isort+flake8，一个工具搞定 |
| 类型检查 | mypy | 严格模式，减少运行时错误 |
| 测试 | pytest + httpx | 单元+集成测试，ASGITransport 直接测 FastAPI |
| 新闻采集 | feedparser + APScheduler | RSS 解析 + 定时任务 |

### 2.2 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    浏览器 / 手机                          │
│              HTMX + Tailwind CSS + Chart.js              │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP
┌──────────────────────▼──────────────────────────────────┐
│                   FastAPI Server                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ Pages    │ │ API      │ │ Auth     │ │ Static   │  │
│  │ (HTML)   │ │ (JSON)   │ │          │ │          │  │
│  └────┬─────┘ └────┬─────┘ └──────────┘ └──────────┘  │
│       │             │                                    │
│  ┌────▼─────────────▼──────────────────────────────┐   │
│  │              Service Layer                       │   │
│  │  blood_sugar | cardiac | medication | visit |    │   │
│  │  wiki | news | alert | backup                   │   │
│  └────────────────────┬─────────────────────────────┘   │
│                       │                                   │
│  ┌────────────────────▼─────────────────────────────┐   │
│  │           SQLAlchemy ORM + Alembic               │   │
│  └────────────────────┬─────────────────────────────┘   │
│                       │                                   │
│  ┌────────────────────▼─────────────────────────────┐   │
│  │              SQLite (WAL mode)                    │   │
│  │              data/chronocare.db                   │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 2.3 项目目录结构

```
/Users/mt16/dev/chronocare/
├── pyproject.toml
├── uv.lock
├── README.md
├── STATUS.md                    # 项目状态（供其他角色读取）
├── DEV_PLAN.md                  # 开发计划（动态更新）
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── Dockerfile
├── docker-compose.yml
│
├── src/
│   └── chronocare/
│       ├── __init__.py
│       ├── main.py              # FastAPI app 入口
│       ├── config.py            # pydantic-settings 配置
│       ├── database.py          # SQLAlchemy engine + session
│       │
│       ├── models/              # ORM 模型
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── person.py
│       │   ├── blood_sugar.py
│       │   ├── cardiac.py
│       │   ├── medication.py
│       │   ├── visit.py
│       │   ├── wiki.py
│       │   └── news.py
│       │
│       ├── schemas/             # Pydantic 请求/响应模型
│       │   ├── __init__.py
│       │   ├── blood_sugar.py
│       │   ├── cardiac.py
│       │   ├── medication.py
│       │   ├── visit.py
│       │   ├── wiki.py
│       │   └── news.py
│       │
│       ├── routers/
│       │   ├── api/             # JSON API（HTMX 调用 + 未来前端）
│       │   │   ├── blood_sugar.py
│       │   │   ├── cardiac.py
│       │   │   ├── medication.py
│       │   │   ├── visit.py
│       │   │   ├── wiki.py
│       │   │   ├── news.py
│       │   │   └── alerts.py
│       │   └── pages/           # HTML 页面路由
│       │       ├── auth.py
│       │       ├── dashboard.py
│       │       ├── blood_sugar.py
│       │       ├── cardiac.py
│       │       ├── medication.py
│       │       ├── visit.py
│       │       ├── wiki.py
│       │       └── news.py
│       │
│       ├── services/            # 业务逻辑
│       │   ├── blood_sugar.py
│       │   ├── cardiac.py
│       │   ├── medication.py
│       │   ├── visit.py
│       │   ├── wiki.py
│       │   ├── news_collector.py
│       │   ├── alert_engine.py  # 预警规则引擎
│       │   └── backup.py
│       │
│       ├── templates/           # Jinja2 模板
│       │   ├── base.html
│       │   ├── components/
│       │   │   ├── nav.html
│       │   │   ├── sidebar.html
│       │   │   ├── person_switcher.html
│       │   │   ├── alert_banner.html
│       │   │   ├── stat_card.html
│       │   │   └── form_fields.html
│       │   ├── dashboard.html
│       │   ├── blood_sugar/
│       │   │   ├── list.html
│       │   │   ├── form.html
│       │   │   └── detail.html
│       │   ├── cardiac/
│       │   ├── medication/
│       │   ├── visit/
│       │   ├── wiki/
│       │   │   ├── list.html
│       │   │   ├── editor.html
│       │   │   └── detail.html
│       │   ├── news/
│       │   └── auth/
│       │       └── login.html
│       │
│       └── static/
│           ├── css/main.css
│           ├── js/
│           │   ├── htmx.min.js
│           │   ├── chart.min.js
│           │   └── app.js
│           └── img/
│
├── data/                        # 运行时数据 (gitignore)
│   ├── chronocare.db
│   └── backups/
│
├── scripts/
│   ├── init_db.py
│   ├── seed_data.py
│   └── collect_news.py
│
├── tests/
│   ├── conftest.py
│   ├── test_models/
│   ├── test_services/
│   └── test_api/
│
├── alembic/
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
│
└── docs/
    ├── development.md
    ├── deployment.md
    └── api.md
```

---

## 3. 功能模块设计

### 3.1 模块总览

| 模块 | 子功能 | 母亲 | 父亲 | MVP | V1 | V2 |
|------|--------|:----:|:----:|:---:|:--:|:--:|
| 老人档案 | 基础信息/疾病标签/紧急联系 | ✅ | ✅ | ✅ | | |
| 血糖管理 | 记录/预警/趋势图/统计 | ✅ | | ✅ | | |
| 心脏指标 | 血压/心率/预警/趋势 | | ✅ | | ✅ | |
| 用药管理 | 药品库/计划/打卡/配药 | ✅ | ✅ | ✅ | | |
| 就诊管理 | 记录/复诊提醒/时间线 | ✅ | ✅ | ✅ | | |
| 健康档案 | 病史/当前病痛/分析 | ✅ | ✅ | | ✅ | |
| 知识库 | 文章/分类/搜索/标签 | ✅ | ✅ | | ✅ | |
| 资讯中心 | RSS采集/浏览/收藏 | ✅ | ✅ | | | ✅ |
| 医疗助手 | 预警/提醒/建议 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 数据备份 | 备份/恢复/导出 | ✅ | ✅ | | ✅ | |

### 3.2 母亲 vs 父亲侧重点对比

| 维度 | 母亲 | 父亲 |
|------|------|------|
| 核心疾病 | 2型糖尿病、高血压 | 心脏病、二尖瓣脱垂 |
| 重点监测 | 血糖（空腹/餐后） | 血压（收缩压/舒张压）+ 心率 |
| 皮肤问题 | 手部湿疹/皮屑 | - |
| 睡眠问题 | - | 失眠、安眠药依赖 |
| 急救关注 | 低血糖急救 | 心梗急救、防猝死 |
| 知识重点 | 糖尿病饮食、高血压管理 | 心脏保养、猝死预防 |

---

## 4. 数据库设计

### 4.1 核心表清单

| 表名 | 用途 | 阶段 |
|------|------|------|
| persons | 老人档案 | MVP |
| conditions | 慢性病/疾病记录 | MVP |
| blood_sugar_records | 血糖记录 | MVP |
| blood_pressure_records | 血压/心率记录 | V1 |
| health_metrics | 通用健康指标（体重等） | V1 |
| medications | 药品库 | MVP |
| medication_plans | 用药计划 | MVP |
| medication_logs | 用药打卡记录 | MVP |
| prescriptions | 配药记录 | MVP |
| visits | 就诊记录 | MVP |
| wiki_categories | 知识分类 | V1 |
| wiki_articles | 知识文章（Markdown） | V1 |
| wiki_fts | FTS5 全文搜索索引 | V1 |
| news_items | 新闻资讯 | V2 |
| rss_feeds | RSS 源配置 | V2 |
| alert_rules | 预警规则 | MVP |
| alert_logs | 预警记录 | MVP |
| activity_logs | 操作日志 | V1 |
| settings | 系统配置 | V1 |

### 4.2 关键设计决策

- **多老人隔离**: 所有数据表通过 `person_id` 外键关联，查询时强制过滤
- **JSON 字段**: 用于灵活扩展属性（过敏史、疾病标签、附件列表）
- **FTS5**: 知识库全文搜索，中文需要安装 jieba 分词或使用 simple 模式
- **预警规则**: JSON 条件表达式，支持灵活配置阈值

---

## 5. 开发计划

### 5.1 Phase 1: MVP (第 1-4 周)

**目标**: 核心数据录入 + 血糖监控 + 用药管理

| 周 | 任务 | 产出 |
|----|------|------|
| W1 | 项目骨架搭建 | uv init, FastAPI 基础路由, 数据库模型, Tailwind 配置 |
| W1 | 老人档案 CRUD | Person 模型, 创建/编辑页面, 顶部切换器 |
| W2 | 血糖管理 | 血糖 CRUD, 预警逻辑, 记录列表页面 |
| W2 | 血糖趋势图 | Chart.js 折线图, 阈值参考线 |
| W3 | 用药管理 | 药品库, 用药计划, 打卡功能 |
| W3 | 就诊记录 | 就诊 CRUD, 复诊提醒 |
| W4 | 仪表盘 | 预警通知, 统计卡片, 近期事件 |
| W4 | 移动端适配 | 响应式布局, 底部 Tab |
| W4 | MVP 测试修复 | Bug 修复, 端到端测试 |

### 5.2 Phase 2: V1 (第 5-7 周)

**目标**: 心脏指标 + 知识库 + 统计分析

| 周 | 任务 | 产出 |
|----|------|------|
| W5 | 心脏指标管理 | 血压/心率 CRUD, 预警, 趋势图 |
| W5 | 健康档案 | 病史记录, 当前病痛 |
| W6 | 知识库 Wiki | Markdown 编辑器, 分类, FTS5 搜索 |
| W6 | 知识库内容 | 初始知识条目（糖尿病/高血压/心脏病/湿疹） |
| W7 | 统计报表 | 周报/月报, CSV 导出 |
| W7 | 数据备份 | 备份/恢复功能 |

### 5.3 Phase 3: V2 (第 8-10 周)

**目标**: 资讯采集 + 提醒系统 + Docker 部署

| 周 | 任务 | 产出 |
|----|------|------|
| W8 | RSS 采集 | feedparser + APScheduler, 本地存档 |
| W8 | 资讯浏览页 | 分类浏览, 收藏, 分享标记 |
| W9 | 用药提醒 | 浏览器通知, 提醒页面 |
| W9 | 数据导入 | Excel/CSV 导入历史数据 |
| W10 | Docker 部署 | Dockerfile, docker-compose |
| W10 | 文档完善 | README, 使用指南, API 文档 |

### 5.4 时间线总览

```
Week  1----2----3----4----5----6----7----8----9----10
      ├─ MVP ──────────┤├─ V1 ────────┤├─ V2 ────────┤
      │骨架│血糖│用药│仪表│心脏│Wiki│统计│RSS │提醒│Docker│
      │档案│趋势│就诊│适配│健康│内容│备份│资讯│导入│文档 │
```

---

## 6. 项目管理规范

### 6.1 STATUS.md 维护规范

```markdown
# ChronoCare STATUS

> 最后更新: YYYY-MM-DD

## 当前阶段: MVP / V1 / V2

## 已完成
- [x] 项目骨架搭建
- [x] 老人档案 CRUD

## 进行中
- [ ] 血糖管理模块

## 待提交改动
- 无

## 下一步计划
- 完成血糖预警逻辑
```

### 6.2 Git 工作流

```
main (稳定) ← feature/xxx (开发) ← 本地改动
    1. git checkout -b feature/xxx
    2. 开发 + 本地测试
    3. pytest 通过
    4. 推送 + PR
    5. Code Review
    6. Merge to main
```

### 6.3 Obsidian 同步

- 项目文档: `tqob/05 Coding/project-chronocare/`
- 每次重大决策/调研/进度更新同步到 Obsidian
- 使用 write_file 直接写入（Obsidian CLI 备选）

---

## 7. 风险评估

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 医疗数据准确性 | 中 | 高 | 仅做记录不做诊断，明确免责声明 |
| SQLite 并发 | 极低 | 低 | 单用户场景，WAL 模式足够 |
| HTMX 学习成本 | 低 | 低 | 用法简单，参考官方示例 |
| 数据丢失 | 低 | 高 | 自动备份 + 手动导出 |
| 开发动力 | 中 | 高 | MVP 快速出成果，每周可运行版本 |

**免责声明**: 本系统仅为健康数据记录工具，不提供医疗诊断。所有健康建议仅供参考，具体诊疗请遵医嘱。

---

## 8. 第一步行动清单

```bash
# 1. 创建项目目录
mkdir -p /Users/mt16/dev/chronocare && cd /Users/mt16/dev/chronocare

# 2. 初始化 Git
git init

# 3. 初始化 uv 项目
uv init --name chronocare

# 4. 安装核心依赖
uv add fastapi uvicorn[standard] sqlalchemy alembic jinja2 pydantic-settings python-multipart httpx bcrypt

# 5. 安装开发依赖
uv add --group dev pytest pytest-asyncio httpx ruff mypy

# 6. 创建目录结构
mkdir -p src/chronocare/{models,schemas,routers/{api,pages},services,templates/{components,blood_sugar,cardiac,medication,visit,wiki,news,auth},static/{css,js,img}}
mkdir -p data scripts tests/{test_models,test_services,test_api} alembic docs

# 7. 创建 STATUS.md 和 DEV_PLAN.md
# 8. 实现 database.py + Person 模型 + 基础路由
# 9. 目标: 第一天结束能在浏览器看到 ChronoCare 首页
```

---

> 本方案基于产品功能调研、UI/UX 设计调研、技术栈评估、测试验收体系四份调研文档整合而成。
> 完整调研文档见 /tmp/chronocare_product_design.md, /tmp/chronocare_uiux_design.md, /tmp/chronocare_devplan_research.md, /tmp/chronocare_test_plan.md
