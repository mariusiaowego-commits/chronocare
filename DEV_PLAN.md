# ChronoCare DEV_PLAN

> 最后更新: 2026-05-13

## Phase 1~3: 已完成 ✅ (2026-04 ~ 05-04)
初始开发阶段，包含 147 路由的完整功能。v0.3.0 精简为 4 核心模块。

## v0.3.0 精简重构 ✅ (2026-05-09)
- [x] 精简为 4 核心功能：人员档案/血糖监控/就诊记录/就医OCR
- [x] 删除 40+ 文件
- [x] MedicalRecord 模型 + CRUD

## v0.4.0 前端重做 ✅ (2026-05-12)

### T3 后端增强 ✅
- [x] 清理已删除功能的残留路由引用
- [x] 新增备份/恢复 API (POST /api/backup, POST /api/backup/restore)
- [x] 核心 API 分页+排序支持 (page, page_size, sort_by, sort_order)
- [x] 创建 static 目录 + manifest.json

### T4 前端重做 ✅
- [x] base.html 重写：GSAP 动画 + 响应式布局 + 深色模式 + PWA
- [x] dashboard.html 重做：Chart.js 血糖趋势 + 预警 + 人员切换
- [x] 人员/血糖/就诊/OCR 全套页面重写
- [x] iPad/Mac 双端适配

### 测试验收 ✅
- [x] ruff lint 全通过
- [x] pytest 2/2 通过
- [x] 全部页面 200 OK
- [x] dashboard 500 错误已修复
- [x] T3+T4 已合并到 main 并 push

### 文档更新 ✅
- [x] 使用指南重写为 v0.4.0 版本
- [x] UI/UX 设计研究文档 (ui-ux-design-guide.md)
- [x] PRD 产品需求说明书 (prd-v0.4.0.md)
- [x] 文档同步到 Obsidian vault

## Phase 4: 下一步 (待规划)

### 高优先级
- [ ] OCR 实际服务集成
  - 方案待选型: PaddleOCR (中文优) / Tesseract / 云API
  - 当前为 mock 占位，需接入真实 OCR 引擎

### 深度分析增强
- [ ] 血糖趋势预测 (移动平均 + 线性回归)
- [ ] 综合健康风险评分 (多指标)
- [ ] 个性化建议生成 (生活方式 + 就医建议)

### 工程改进
- [ ] pyproject.toml version 更新为 0.4.0
- [ ] iPad 实机测试
- [ ] 本地打包 (.app)

## 下一步行动
1. OCR 方案选型与集成
2. iPad 实机验证响应式体验
3. 新功能开发用 worktree 工作流 (feature branch → PR → merge)
