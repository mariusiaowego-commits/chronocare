# chronocare AGENTS

老年父母健康管理平台 — 精简版，专注核心功能。

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

## Git 工作流
- **feature branch → commit → PR（未测不推）**
- 单人开发，不用 worktree，直接在本地拉 feature branch
- 分支命名: `feat/<功能名>` 或 `fix/<bug名>`
- 流程: `git checkout -b feat/xxx` → 开发 → commit → push → PR → merge → 删分支
- GitHub push/pull 用 SSH（fallback HTTPS: `git config --local remote.origin.pushurl https://github.com/mariusiaowego-commits/chronocare.git`）
- main 保持干净，所有改动走 feature branch

## 收尾文档
- STATUS.md — 项目根目录
- DEV_PLAN.md — 项目根目录
- vibe-coding-log/ — 项目根目录，按日期记录
- wiki — `hermes-base/projects/project-chronocare.md`

## 收尾 Checklist（每次会话结束前必须执行）


```
□ STATUS.md — 本次修改涉及的功能，对应条目是否更新（日期 + 阶段描述）
□ vibe-coding-log — 新增当日记录，append 到文件开头
□ handoff-YYMM-DD.md — 完整记录含待办清单，写入项目根目录
□ Git — 测通后 add → commit → feature branch → PR（未测不推）
□ Git push — 确保所有 commits 推送到 origin
□ README — 本次改动需要同步更新文档
□ 服务验证 — curl 页面确认 200 OK
□ 用户确认 — 展示最终结果
□ Wiki沉淀 — 发现新模式/踩坑记录/项目惯例，同步到 hermes-base/projects/
```

触发条件（任一）：有新 commits / STATUS.md 变化 / 新增或删除功能模块 / 版本号变更。

防漂移：handoff 日期必须 >= STATUS.md 最后更新日期，过期立即更新（晨检 cron 也会检查）。
