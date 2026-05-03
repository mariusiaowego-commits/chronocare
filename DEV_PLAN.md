# ChronoCare DEV_PLAN

> 最后更新: 2026-05-03

## Phase 1: MVP (第 1-4 周)

### W1: 项目骨架 + 老人档案
- [x] uv init + 依赖安装
- [x] src/chronocare/ 目录结构
- [x] SQLAlchemy 模型 (全部)
- [x] Alembic 初始化
- [ ] Person CRUD API + 页面
- [ ] 顶部老人切换器
- [ ] 首次 Alembic migration

### W2: 血糖管理
- [ ] 血糖记录 CRUD
- [ ] 血糖预警逻辑 (空腹>=7.0, 餐后>=10.0)
- [ ] 血糖趋势图 (Chart.js)
- [ ] 血糖统计卡片

### W3: 用药管理 + 就诊记录
- [ ] 药品库 CRUD
- [ ] 用药计划 + 打卡
- [ ] 配药记录
- [ ] 就诊记录 CRUD
- [ ] 复诊提醒

### W4: 仪表盘 + 移动端
- [ ] 预警通知展示
- [ ] 统计卡片
- [ ] 近期事件时间线
- [ ] 响应式布局 (移动端底部 Tab)
- [ ] MVP 测试修复

## Phase 2: V1 (第 5-7 周)
- 心脏指标管理
- 健康档案
- 知识库 Wiki (Markdown + FTS5)
- 统计报表 + 数据备份

## Phase 3: V2 (第 8-10 周)
- RSS 资讯采集
- 用药提醒
- Docker 部署
