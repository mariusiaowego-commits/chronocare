# ChronoCare DEV_PLAN

> 最后更新: 2026-05-20

## Phase 1~3: 已完成 ✅ (2026-04 ~ 05-04)
初始开发阶段，包含 147 路由的完整功能。v0.3.0 精简为 4 核心模块。

## v0.3.0 精简重构 ✅ (2026-05-09)
- [x] 精简为 4 核心功能：人员档案/血糖监控/就诊记录/就医OCR
- [x] 删除 40+ 文件
- [x] MedicalRecord 模型 + CRUD

## v0.4.0 前端重做 ✅ (2026-05-12)
- [x] 后端增强: 清理残留路由 + 备份 API + 分页排序
- [x] 前端重写: GSAP + Chart.js + 响应式 + 深色模式 + PWA
- [x] 测试验收: lint + pytest + 全页面验证
- [x] 文档更新: 使用指南 + PRD + UI/UX 设计文档

## v0.5.0 OCR Pipeline ✅ (2026-05-13~05-14)
- [x] T1: Swift OCR 脚本 + Python subprocess 封装
- [x] T2: LLM 结构化解析器 (4 种 prompt 模板, 9 tests)
- [x] T3: 集成 Pipeline 替换全部 mock 实现
- [x] T4: 端到端测试 (27/27 通过) + OCR 展示优化 + 文档

## v0.5.0 血糖趋势分析 ✅ (2026-05-14)
- [x] 移动平均 (7天/14天)
- [x] 线性回归预测
- [x] TIR (Time in Range) 计算
- [x] CV (变异系数)
- [x] 智能预警 (连续高/低血糖)
- [x] Chart.js 可视化 (折线图 + 饼图)

## v0.5.0 OCR 方案 A ✅ (2026-05-18)
- [x] 架构决策: 应用不依赖 OPENROUTER_API_KEY，OCR 全部走 hermes agent 层面 vision_analyze
- [x] 输出规范化层: `normalize_lab_results` / `normalize_doctor_orders` / `normalize_structured_data`
- [x] 降级处理: 无 API key 时返回 error JSON 而非崩溃
- [x] 测试: 41/41 通过 (原27 + 新14规范化测试)
- [x] chronocare-ocr skill: 完整 harness — prompt 模板 + 字段映射 + API 调用 + 验收清单

## 生产验收 ✅ (2026-05-18)
- [x] T0-T5 全部通过
- [x] 真实化验单端到端验证: 钱精华（上海市老年医学中心，内分泌科）

## Phase 6: 下一步规划

### 功能增强
- [ ] 多页化验单支持：PDF 转图片后连续识别和合并
- [ ] 综合健康风险评分 (多指标)
- [ ] 个性化建议生成 (生活方式 + 就医建议)

### 工程改进
- [ ] iPad 实机测试
- [ ] 本地打包 (.app)
- [ ] DESIGN.md 设计落地 (字体/配色/图标替换)
- [ ] 重构 ruff 警告清理 (B007/UP015)
- [ ] chronocare-ocr skill 流程验证（真实化验单图片端到端）

## 下一步行动
1. 用真实化验单图片走一遍 chronocare-ocr skill 流程验证
2. 新功能开发用 worktree 工作流 (feature branch → PR → merge)
3. 清理 DB 测试数据前先备份
