# 260609-health-report-handoff.md

> 生成时间: 2026-06-09(下午,健康报告图 session)
> 当前版本: v0.5.0
> 分支: main (commit f4eaa8e)
> 关联 commit: 本次 session **未产生 git commit**(PRD 还在用户审阅,等 OK 后再随 T1 实施一并 commit)

---

## 本次 Session 完成

### 1. tjh 病例汇总分析 (基于现有 DB)
- 跑了 `scripts/analyze_tjh_history.py`(本 session 落地的脚本,见下方"关键文件")
- 回答了用户 3 个分析问题:
 1. 过去看哪个医生更多 → 张培培 7 / 杨力凡 6 / 崔洁 5
 2. 不同医生诊断是否一致 → 心内科 4 项完全一致(房颤、二尖瓣反流、高血压、慢性失眠),差异来自专科会诊
 3. 过去到现在病情变化 → 心血管主病稳定,但有 4 项需关注(二尖瓣需手术评估 / 失眠加重 / INR 波动 / 新发呼吸疾病)

### 2. 信息图手动生成(v1 → v2 → v3 三轮迭代)
- v1: morandi-journal + winding-roadmap,术语专业 → 老人听不懂
- v2: 过度温和,去掉"中风/出血/倒漏" → 把"需手术评估"改成"慢慢聊不着急" → **矫枉过正,会误导病人**
- **v3 (最终版)**: 医学准确 + 措辞温和,用色区分(橄榄绿=稳定 / 陶土橘=需治疗)
- CDN: https://v3b.fal.media/files/b/0a9d9209/7AW3pUUXindc7TYtWrzRd_4o1sf1Yd.png
- **待用户确认是否下载到 ~/Downloads/**

### 3. 关键学习沉淀(已在 vibe-coding-log/2026-06-09.md)
- **OCR 噪声过滤**: 两轮策略(高频锚定 + 白名单召回)
- **同日期多 PDF 配对**: 找医生归属时关键
- **"温和 ≠ 淡化病情"**: 健康物料要同时准确 + 不戏剧化

### 4. ChronoCare 健康报告图 Feature PRD v2 ✅
- **核心需求**: 把"LLM 分析 + 信息图"做成 feature,前端点击生成
- **2 种格式**: PC 版(已验证) + Mobile 版(等老人版 research 定)
- **多用户支持**: 适用于 ChronoCare 内**所有 Person**,不只是 tjh
- **快照策略**: 选项 A — 全存(prompt + data + image),data 用 gzip 压缩存 LargeBinary
- **实施策略**: Kanban orchestrator 拆 7 个任务(T1~T7)分阶段并行

---

## 待处理事项(下一步行动)

### ⏸️ **当前阻塞点: 用户改 model**
用户原话: "我感觉我目前chat使用的model有点问题 我要先改一下"
- 用户去配置/切换 LLM model,本会话暂停
- 用户改完回来会继续审 PRD v2

### 用户回来后,严格按这个顺序走:

1. **等用户 OK PRD v2**
 - PRD 路径: `/Users/mt16/dev/chronocare/docs/产品功能设计/health-report-prd.md`
 - Obsidian 镜像: `/Users/mt16/Library/Mobile Documents/iCloud~md~obsidian/Documents/tqob/05-Coding/project-chronocare/docs/prd-health-report-2026-06-09.md`
 - 用户逐项确认,如改: 直接告诉我哪里,改完 → 同步双份 → 继续

2. **用户 OK 后: dispatch Kanban workers**(按 PRD §7)
 - **T1 (foundation, ready)**: 后端数据聚合层 + `ReportGeneration` model + Alembic migration + POST/GET API 骨架 → backend-eng / worktree `wt/health-report-foundation`
 - **T2 (research, ready)**: 老人版物料设计 research,输出 MD 到 obsidian `[[health-report-for-elderly-research]]` → researcher 角色
 - T3/T5/T6 后续按 PRD §7.1 任务图按依赖启动

3. **dispatch 命令模板**(供新会话直接复制)
 ```bash
 # T1 — 后端 foundation
 hermes kanban --board chronocare create "T1: 健康报告 feature foundation — 数据聚合 + DB + API" \
 --assignee backend-eng --workspace worktree --branch wt/health-report-foundation \
 --body "$(cat /tmp/t1_body.md)"
 # T2 — 老人版 research(并行)
 hermes kanban --board chronocare create "T2: 老人版微信分享物料设计 research" \
 --assignee researcher \
 --body "$(cat /tmp/t2_body.md)"
 ```
 T1 / T2 的 body 文件需根据 PRD §7.2 + §5.2 写明 acceptance criteria / 必答 5 个问题。

4. **T7 整合阶段**(所有 worker done 后): 跑 pytest + ruff + 自己浏览器端到端验证 + commit + PR

### 重要注意事项(给新会话)

- **不要抢跑**: 用户的"PRD 逐项确认"习惯必须遵守,改完再改再 sync,**不能跳过审阅直接 dispatch**
- **不要替用户做模型决策**: 用户已经表达 model 不对,等他改完回来
- **大文件 / 重要产物路径见下表**

---

## 关键文件

| 文件 | 说明 | 状态 |
|---|---|---|
| `scripts/analyze_tjh_history.py` | 本 session 新增 — tjh 数据聚合脚本,可复用为 service 基础 | ✅ git 未追踪(本 session 改动) |
| `docs/infographics/tjh-history-2026-06-09/` | 信息图全套产物(source.md / analysis.md / structured-content.md / prompts/infographic.md) | ✅ git 未追踪 |
| `docs/产品功能设计/health-report-prd.md` | PRD v2 (本 session 产出) | ✅ git 未追踪 |
| `vibe-coding-log/2026-06-09.md` | 本 session 日志(本版覆盖了早上云胶片那版,因为本 session 是独立主题) | ⚠️ 早上的云胶片内容**丢了一部分** |
| `obsidian: prd-health-report-2026-06-09.md` | PRD 双份镜像 | (Obsidian vault,不算 git) |
| `obsidian: mrd-用户健康报告生图需求.md` | 用户原始 MRD,已加 `landed_prd:` 反向引用 | (Obsidian vault) |

⚠️ **重要**: **本 session 没有产生任何 git commit**。所有改动都在 working tree。等 T1 实施时一起 commit 到 `wt/health-report-foundation`,保持 PR 原子性。

---

## 技术决策(本 session 沉淀)

1. **OCR 噪声过滤的两轮策略**: 高频锚定(>=2 次的签名视为医生)+ 白名单召回。已用于 analyze_tjh_history.py 提取医生。
2. **信息图设计"准确 + 温和"天平**:
 - 口语解释必须有(老人能懂)
 - 医学术语必须保留(家属和医生能懂)
 - 风险词必须出现但要平和(用"出血风险↑"而非"出血危险!!")
 - 用色区分状态(橄榄绿=稳定 / 陶土橘=需治疗)
3. **PRD 同步双份**: repo + obsidian 各一份,frontmatter 互相加 sync / source_mrd 字段建立双向追溯
4. **数据快照 gzip + LargeBinary**: 比纯字符串存节省 60-80% 空间,应用层透明

---

## 待办清单(checklist)

### 本 session 已完成
- [x] tjh 数据分析三问
- [x] 信息图 v3 (准确+温和版)
- [x] 信息图全套产物落地到 docs/infographics/tjh-history-2026-06-09/
- [x] analyze_tjh_history.py 脚本落地
- [x] 健康报告图 PRD v2 双份同步(repo + obsidian)
- [x] MRD 文件加反向引用 `landed_prd`
- [x] 工作流方法沉淀到 vibe-coding-log/2026-06-09.md

### 用户回来后
- [ ] **用户改完 model** (用户去做)
- [ ] 用户审 PRD v2,如改则同步双份
- [ ] 用户 OK → dispatch T1 + T2 Kanban workers 并行
- [ ] v3 信息图下载到 ~/Downloads/(可选,用户决定)
- [ ] 用户切换 model 后报告观察是否更稳定

### 后续(PRD 落地后)
- [ ] T1 完成后 → 启动 T3 (PC 版生成)
- [ ] T2 完成后 → 启动 T4 + T5 (Mobile 版)
- [ ] T6 前端 modal + 历史
- [ ] T7 整合测试 + PR + merge
- [ ] 收尾文档(STATUS / handoff / vibe-log / git push / 沉淀到 wiki)

---

## 关联资源

- **PRD**: `docs/产品功能设计/health-report-prd.md` (双份同步)
- **MRD**: obsidian `tqob/05-Coding/project-chronocare/docs/mrd-用户健康报告生图需求.md`
- **v3 信息图 CDN**: https://v3b.fal.media/files/b/0a9d9209/7AW3pUUXindc7TYtWrzRd_4o1sf1Yd.png
- **历史 handoff**: `260609-handoff.md`(早上的云胶片 session)— 与本 handoff 互补
- **STATUS.md**: 项目根,本 session 未更新(因为没有 commit,等 T1 完成一并更新)

---

## 自我沉淀(给未来的我)

1. **PRD 不要等"完美"才落地** — v1 → v2 已经够启动用户审阅,迭代优于空想
2. **健康物料措辞要"双轨"** — 口语 + 医学术语同时给(括号法),既不吓人不淡化
3. **OCR 噪声过滤两轮策略值得记住** — 可推广到任何文档解析场景
4. **PRD 双份同步(repo + obsidian)是习惯**,frontmatter 互相加 sync 字段降低漂移
5. **用户表达 model 问题时不要替他决策** — 等他自己改,改完再观察

---

**如果你是新会话接手这份 handoff:**
1. 先读 PRD §1-3 理解产品
2. 读"待办清单"里"用户回来后"那段
3. 等用户回来后说"OK 开干"再 dispatch workers
4. **不要**绕过 PRD 审阅直接动手