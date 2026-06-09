---
title: ChronoCare 健康报告图 (Health Report Generator) PRD
description: 一键汇总用户在 ChronoCare 的全部健康数据,生成可视化海报(PC + Mobile 两版),适合家庭健康档案与微信分享给老人
project: chronocare
created: 2026-06-09
status: draft v2 (multi-user + snapshot strategy confirmed)
sync: /Users/mt16/Library/Mobile Documents/iCloud~md~obsidian/Documents/tqob/05-Coding/project-chronocare/docs/prd-health-report-2026-06-09.md
tags:
  - prd
  - health-report
  - chronocare
  - baoyu-infographic
  - feature-design
---

# ChronoCare 健康报告图 — PRD

> 📌 **本 PRD 已同步到 Obsidian vault**: `tqob/05-Coding/project-chronocare/docs/prd-health-report-2026-06-09.md`
> 🎨 **设计基础**: 复用 baoyu-infographic skill,已通过 3 轮手动迭代(v1 → v2 → v3)验证"准确 + 温和"的措辞天平

## 1. 背景与动机

**用户场景**:家里所有需要长期追踪健康状况的老人(以及其他需要管理的家庭成员),他们在 ChronoCare 里有完整的就诊记录、血糖记录、医疗档案 OCR。家属(用户本人)希望对其中任意一个成员,**一键生成可视化健康报告**:老人自己看得懂、家属一起看、方便微信发给亲友。

**适用范围**:ChronoCare 内的**所有 `Person` 记录**都是潜在用户,不是只针对 tjh。当前数据库示例:tjh(父亲,主案例)、qian(母亲)等 — 每个 Person 都能独立生成报告,互不影响。

**已验证的原型**:2026-06-09 我们在 tjh 上手动跑通了完整链路 — 用 `scripts/analyze_tjh_history.py` 聚合数据 + baoyu-infographic skill 生成 morandi-journal + winding-roadmap 风格的信息图,经 3 轮迭代后得到准确 + 温和的 v3 版本。该脚本的输入参数是 `person_id`,扩展到所有 Person 不需要改动核心逻辑。

**核心痛点**(为什么需要做成 feature):
1. **重复劳动**:每次想看报告都要手动跑脚本,不能给家属自助用
2. **多用户**:家里老人不止一位(母亲、岳父母等),每个人都需要独立报告
3. **数据格式不可控**:手动 prompt 出来的图每次措辞、配色都可能不同,不利于"家庭档案"长期一致性
4. **Mobile 版缺位**:PC 版(morandi 路线图)在手机上字太小、信息太密,老人看不清;微信分享给老人需要专门的 mobile 版
5. **没有历史记录**:每次生成的图丢失,无法对比前后变化

## 2. 目标与非目标

### 目标 (v1.0)
- 对 ChronoCare 中**任意一个 Person** 一键生成健康报告图(默认对当前选中的人,也支持在 Dashboard 选人)
- 同时支持 **PC 版**(详细,A4 打印友好)与 **Mobile 版**(大字、简洁、微信分享友好)
- 老人看的 mobile 版要明确区分"稳定"vs"需进一步治疗",既不吓人也不淡化
- 报告内容、措辞、色调有标准化模板,确保每次生成质量稳定
- 每个 Person 都有独立的报告历史,可查、可对比

### 非目标 (v1.0 不做)
- ❌ 自动定时生成报告(用户手动触发即可)
- ❌ LLM 实时解读/对话(本版本只生成静态图)
- ❌ 多语言 i18n(只做中文)
- ❌ 第三方分享 API 集成(微信分享靠用户手动截图)
- ❌ PDF 导出(mobile 版只输出图片,PC 版可考虑后续)

## 3. 用户故事

| ID | 角色 | 故事 |
|---|---|---|
| US-1 | 家属(用户) | 在 Dashboard 点击"生成健康报告",弹出 Person 选择器(默认选中当前 person)→ 选完 → 弹出 PC/Mobile 选择框 → 5 秒内看到预览图 |
| US-1b | 家属 | 在某个 Person 的详情页直接点击"生成报告"按钮,跳过 Person 选择,直接弹 PC/Mobile 选择框 |
| US-2 | 家属 | 生成后可下载 PNG / 复制链接 / 直接发给微信好友 |
| US-3 | 老人 | 收到微信图片,能看清文字、识别颜色含义(绿=稳定、橘=需治疗),知道下一步要做什么 |
| US-4 | 家属 | 进入某个 Person 的报告历史列表,按时间排序看历史报告,可对比前后变化 |
| US-5 | 家属 | 想给岳母也生成一份 → Dashboard 切换 Person → 同样的流程(每个人独立) |

## 4. 产品形态

### 4.1 前端 UI 位置
- **Dashboard 主页**:在 "快捷操作" 区域新增按钮 **"📊 生成健康报告"**
 - 点击 → 弹出 **Person 选择器**(列出所有 Person,默认选中当前 person)
 - 选完 → 弹出 PC/Mobile 选择框(后续流程)
- **Person 详情页**:每个 Person 页面右上角加一个 **"📊 生成报告"** 按钮(细粒度触发,**跳过 Person 选择**)
- 点击选择版本后弹出 **modal**,内容:
 - 顶部:该人员基本信息(姓名/年龄/数据概览)
 - 中部:**两份版式并排预览**(PC + Mobile 各一张缩略图)
 - 用户选其中一份 → 点击 **"生成完整版"**
 - 加载态(预计 5~15 秒) → 显示完整图 + 下载按钮 + 关闭按钮
- **报告历史列表**:Person 详情页下方新增 "📋 健康报告历史" 区块,按时间倒序列出该人的所有报告(缩略图 + 链接)

### 4.2 数据模型:ReportGeneration
新增表 `report_generations`:

```python
class ReportGeneration(Base):
    __tablename__ = "report_generations"

    id: int (PK)
    person_id: int (FK → persons.id)
    layout: str  # "pc" | "mobile"
    status: str  # "pending" | "generating" | "completed" | "failed"
    image_url: str | None  # 本地路径或 CDN URL
    prompt_snapshot: str  # 当时用的 prompt(便于复现/调试)
    data_snapshot: LargeBinary  # gzip 压缩的 JSON 快照(节省空间,应用层透明加解压)
    error_message: str | None
    generation_seconds: float | None
    created_at: datetime
    completed_at: datetime | None
```

### 4.3 API 端点

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/api/persons/{person_id}/reports/generate` | 异步触发生成,返回 task_id |
| GET | `/api/reports/{task_id}` | 查询生成状态 + 结果 |
| GET | `/api/persons/{person_id}/reports` | 该人员的报告历史列表 |
| GET | `/api/reports/{task_id}/image` | 返回图片文件 |

### 4.4 后端生成流程

```
[POST /api/persons/{id}/reports/generate?layout=mobile]
    ↓
[1. 数据聚合层 services/report_data.py]
  - 读 visits / medical_records / blood_sugar_records
  - 复用 analyze_tjh_history.py 的核心逻辑,封装为函数
  - 输出统一 JSON 结构(医生统计/诊断时间线/INR 变化/对比)
    ↓
[2. Prompt 组装层 services/report_prompts.py]
  - 选 layout × style 模板(PC = morandi-journal + winding-roadmap,
                           Mobile = morandi-journal + 简化结构)
  - 根据 layout 选择对应 prompt 模块(separate templates)
  - 把数据 JSON 填进模板,生成最终 prompt
    ↓
[3. 图像生成层 services/report_image.py]
  - 调用 image_generate(prompt, aspect_ratio)
  - PC 版 → portrait (3:4)
  - Mobile 版 → square (1:1) 或 portrait (9:16) — **待 research 后定**
  - 返回 image URL
    ↓
[4. 持久化层]
  - 下载到 data/reports/{person_id}/{task_id}.png
  - 更新 DB report_generations 表
    ↓
[5. 通知前端]
  - 前端轮询 GET /api/reports/{task_id}
  - status=completed → 返回 image_url
```

## 5. Mobile 版专项要求 (需 Research 驱动)

### 5.1 与 PC 版的核心差异

| 维度 | PC 版 (已验证) | Mobile 版 (待 design) |
|---|---|---|
| 尺寸 | portrait 3:4 (A4) | **待 research 决定**(可能是 1:1 或 9:16) |
| 信息密度 | 高 — 6 站点路线图 + 4 bento 卡 + 4 便签 | **低 — 仅核心 3~5 个信息块** |
| 文字大小 | 正文中等 | **大字,正文 > 24px 等效** |
| 布局复杂度 | winding-roadmap + bento | **单列垂直,卡片堆叠** |
| 视觉吸引力 | morandi 学术感 | **更温暖、更"礼物"感**(适合微信分享) |

### 5.2 Research 必须回答的问题

1. **微信里老人最容易接受的图片尺寸** — 1:1 / 4:5 / 9:16 / 16:9?数据来源:微信设计规范、适老化设计指南、相关行业调研
2. **老年人视觉衰退的关键阈值** — 字号、色对比、留白比例的最低要求
3. **微信生态"礼物感"设计的元素** — 配色、装饰、情绪曲线(参考:家庭相册/回忆录/朋友圈长辈图)
4. **认知负荷控制** — 单图最多容纳多少个独立信息块?老人能记住几个?
5. **吸引老人持续看的元素** — 故事性?人物头像?家庭元素?色彩情绪?

### 5.3 Research 输出要求

- 文件:`/Users/mt16/Library/Mobile Documents/iCloud~md~obsidian/Documents/hermes-base/projects/project-chronocare/health-report-for-elderly-research.md`
- 内容:研究方法 + 关键发现 + 设计建议 + 参考文献
- 引用真实来源(微信适老化白皮书 / Apple Accessibility Guidelines / NN/g 老年用户研究 / 国内适老化设计案例)
- 结论必须是可操作的(每个建议带具体数字/例子)

### 5.4 Research → 设计转化
研究产出作为 `services/report_prompts.py` 里 mobile 模板的设计依据,prompt 里引用具体设计参数。

## 6. 技术栈与依赖

| 类别 | 选择 | 理由 |
|---|---|---|
| 后端框架 | FastAPI (沿用) | 项目已有,无新增依赖 |
| 数据库 | SQLite + SQLAlchemy 2.0 (沿用) | 同上 |
| ORM 模型 | 新增 `ReportGeneration` model + Alembic migration | 与现有 models 同构 |
| LLM 客户端 | Hermes image_generate (Nous subscription) | 沿用 dizical-report / chronocare-ocr 模式 |
| 数据聚合 | 复用 `scripts/analyze_tjh_history.py` 的核心函数 | 已有验证 |
| 前端 | HTMX + Tailwind (沿用) | 项目模板机制 |
| 异步任务 | **FastAPI BackgroundTasks** (简单场景) 或 **arq / celery**(若需重试) | v1.0 先用 BackgroundTasks |
| 文件存储 | 本地 `data/reports/{person_id}/{task_id}.png` | 与现有 `uploads/` 一致 |
| 测试 | pytest + httpx AsyncClient (沿用) | 项目已有测试框架 |

## 7. Kanban Orchestrator 实施策略

### 7.1 任务分解原则
- **T1 (foundation, ready)**: 数据聚合层 + ReportGeneration model + Alembic migration + POST/GET API 骨架。这是后续所有任务的依赖,先做。
- **T2 (research, parallel with T1)**: 老人版物料设计 research,输出 MD 到 obsidian。这个不阻塞代码,可以并行。
- **T3 (PC 版生成, parent: T1)**: PC 版 prompt 模板 + image 调用 + 持久化。
- **T4 (Mobile 版 prompt, parent: T2)**: 基于 research 产出,设计 mobile 版 prompt。
- **T5 (Mobile 版生成, parent: T1, T4)**: Mobile 版 image 生成 + 持久化。
- **T6 (前端 modal + 历史记录, parent: T1)**: HTMX modal + 历史列表 UI。
- **T7 (集成测试 + PR, parent: T3, T5, T6)**: E2E 测试 + docs 更新 + PR 提交。

### 7.2 Worker 分工
- `backend-eng`: T1, T3, T5(代码实现)
- `researcher`: T2(独立任务)
- `frontend-eng`: T6(UI 工作)
- `coder`: T7(整合 + 测试,本 session 内完成)

### 7.3 分支策略
- T1: `wt/health-report-foundation` (worktree)
- T3: `wt/health-report-pc`
- T5: `wt/health-report-mobile`
- T6: `wt/health-report-frontend`
- T7: 整合到 main

每个 worker 用独立分支,避免 moni 教训(worktree 串台)。

### 7.4 风险与防御
- **Image 生成可能失败 / 超时**:DB 状态机管理(`pending → generating → completed/failed`),前端轮询显示进度
- **Prompt 漂移**:每次生成时把 prompt snapshot 存进 DB,便于复现
- **数据量变化**:medical_records 可能有几百条,数据聚合必须先有 schema 校验 + 量级保护(>1000 条时给出提示而非崩溃)
- **老人版研究周期不可控**:T2 用 `--triage` 启动,T5 等 T2 完成才能开始。T3 不依赖 T2,可先行。

## 8. 验收标准

### 8.1 功能验收
- [ ] Dashboard 与 Person 详情页都有"生成健康报告"按钮
- [ ] Dashboard 按钮点击后弹出 Person 选择器,可选任意 Person
- [ ] Person 详情页按钮跳过选择器,直接对该人生成
- [ ] 点击后弹出 modal,显示 PC + Mobile 两个缩略图
- [ ] 选择某版本后 5~15 秒内返回完整图
- [ ] 图片正确持久化到 `data/reports/{person_id}/`
- [ ] 该 Person 报告历史可在其详情页查看(按时间倒序)
- [ ] **多用户隔离**:qian 生成的报告不会出现在 tjh 的历史里,反之亦然
- [ ] **重复生成**:同一 Person 同一 layout 可多次生成,每次都是新记录
- [ ] 重复生成同一版本,数据快照正确反映当前 DB 状态

### 8.2 质量验收
- [ ] 老人版(mobile)字足够大、配色清晰、信息密度低
- [ ] PC 版与今日手动生成的 v3 一致(配色/结构/措辞)
- [ ] 措辞符合"准确 + 温和"原则(经过今日 3 轮迭代验证)
- [ ] 数字精准(医生次数 / INR 数值等)
- [ ] 模板覆盖老人版研究的全部设计建议

### 8.3 工程验收
- [ ] Alembic migration 干净运行
- [ ] pytest 通过(单元测试 + API 测试)
- [ ] ruff check 通过
- [ ] 所有 commit 留痕在 gh
- [ ] PR review 通过后 merge 到 main
- [ ] STATUS.md / handoff / vibe-log 同步更新

## 9. 时间盒 (估算)

| Phase | 任务 | 估时 |
|---|---|---|
| PRD 评审 | 等待用户 OK | 用户确认时间 |
| Research | T2 老人版设计研究 | 2~4 小时(独立 worker) |
| 后端 foundation | T1 数据聚合 + DB + API | 3~5 小时(独立 worker) |
| PC 版 | T3 prompt + image | 1~2 小时(在 T1 完成后) |
| Mobile 版 | T4+T5 prompt + image | 2~3 小时(在 T1+T2 完成后) |
| 前端 | T6 modal + 历史 | 2~3 小时(在 T1 完成后) |
| 整合 | T7 测试 + PR + docs | 1~2 小时 |

总估时:**约 12~20 小时**(跨多 worker 并行后)

## 10. Out of Scope (明确不做)

- 自动定时生成 (cron 推送)
- LLM 实时对话/问答
- 多语言
- 微信分享 API 集成
- PDF 导出
- 报告对比 / diff 功能
- 多人报告合并(每个 person 一份独立报告)

---

## 11. 已确认的关键决策

### 11.1 数据快照策略 — 选项 A:存全部 ✅
**决策**:报告生成时,把当时用的 **prompt 全文 + data 快照 + image_url + 元数据** 全部存到 `report_generations` 表。

**理由**:
- 今天手动跑的过程中改了 3 次 prompt,每次都靠 data snapshot 才能对比哪版更好
- 调试失败时,能用同一份 prompt + data 精确复现
- 未来若调整模板,可以重跑历史快照生成新版(实验性)
- 占空间可控:单个快照 ~10~30 KB,即便 1000 次生成也只有 30 MB

**额外优化**:为了节省空间,`data_snapshot` 字段可以用 gzip 压缩后存(blob),用 SQLAlchemy 的 `LargeBinary` 类型。应用层压缩/解压透明。

### 11.2 多用户支持 — 所有 Person ✅
**决策**:本 feature 对 ChronoCare 中**所有 `Person` 记录**开放,不是 tjh 专属。

**实现要点**:
- API 路径已是 `/api/persons/{person_id}/reports/...` — 天然支持多用户
- Dashboard 的"快捷操作"按钮触发时,需要先选 Person(弹一个 person picker)
- Person 详情页直接对该人生成
- 数据隔离靠 `person_id` 外键,查询时必须按 person 过滤
- 报告历史列表按 `person_id` 分组展示

### 11.3 报告按人隔离 ✅
每个 Person 的报告独立存储与展示,不允许跨人合并、不允许"全家福"报告(超出 v1.0 范围)。

---

**等你回 OK / 调整后,我立刻开干 Phase 2 (research 任务 dispatch)。**