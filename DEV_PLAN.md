# ChronoCare DEV_PLAN

> 最后更新: 2026-05-13

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

## v0.5.0 OCR Pipeline ✅ (2026-05-13)
- [x] T1: Swift OCR 脚本 + Python subprocess 封装
- [x] T2: LLM 结构化解析器 (4 种 prompt 模板, 9 tests)
- [x] T3: 集成 Pipeline 替换全部 mock 实现
- [x] T4: 端到端测试 (27/27 通过) + OCR 展示优化 + 文档

## Phase 6: 下一步 (待规划)

### 功能增强
- [ ] 血糖趋势预测 (移动平均 + 线性回归)
- [ ] 综合健康风险评分 (多指标)
- [ ] 个性化建议生成 (生活方式 + 就医建议)

### 工程改进
- [ ] iPad 实机测试
- [ ] 本地打包 (.app)
- [ ] DESIGN.md 设计落地 (字体/配色/图标替换)

## 下一步行动
1. iPad 实机验证响应式体验
2. 新功能开发用 worktree 工作流 (feature branch → PR → merge)
