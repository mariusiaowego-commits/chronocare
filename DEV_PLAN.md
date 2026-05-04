# ChronoCare DEV_PLAN

> 最后更新: 2026-05-04

## Phase 1: MVP (第 1-4 周) ✅ 已完成

### W1: 项目骨架 + 老人档案 ✅
- [x] uv init + 依赖安装
- [x] src/chronocare/ 目录结构
- [x] SQLAlchemy 模型 (全部)
- [x] Alembic 初始化
- [x] Person CRUD API + 页面
- [x] 顶部老人切换器
- [x] 首次 Alembic migration

### W2: 血糖管理 ✅
- [x] 血糖记录 CRUD
- [x] 血糖预警逻辑 (空腹>=7.0, 餐后>=10.0)
- [x] 血糖趋势图 (Chart.js)
- [x] 血糖统计卡片

### W3: 用药管理 + 就诊记录 ✅
- [x] 药品库 CRUD
- [x] 用药计划 + 打卡
- [x] 配药记录
- [x] 就诊记录 CRUD
- [x] 复诊提醒

### W4: 仪表盘 + 移动端 ✅
- [x] 预警通知展示
- [x] 统计卡片
- [x] 近期事件时间线
- [x] 响应式布局 (移动端底部 Tab)
- [x] MVP 测试修复

## Phase 2: V1 (第 5-7 周) 🔄 进行中

### 已完成
- [x] 知识库 Wiki (Markdown + FTS5)
- [x] RSS 资讯采集
- [x] 统计报表: 血糖/血压趋势图 + CSV 导出
- [x] 数据备份/恢复

### 待完成
- [ ] 心脏指标管理增强
- [ ] 健康档案汇总
- [ ] 统计报表增强 (更多图表类型)

## Phase 3: V2 (第 8-10 周)
- [ ] 用药提醒 (定时通知)
- [ ] Docker 部署 (跳过)
