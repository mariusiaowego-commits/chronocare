# ChronoCare STATUS

> 最后更新: 2026-05-04

## 当前阶段: Phase 2 进行中

## 已完成
- [x] 产品功能调研与设计
- [x] 技术栈评估与选型
- [x] UI/UX 设计方案
- [x] 数据库表结构设计
- [x] 测试验收体系设计
- [x] 三阶段开发计划制定
- [x] 项目骨架搭建 (uv + src/chronocare/ + FastAPI + SQLAlchemy)
- [x] Alembic 迁移 (init + wiki_news)
- [x] Person CRUD (API + 模板 + HTMX)
- [x] 血糖记录 CRUD (API + 页面)
- [x] 血压记录 CRUD (API + 页面)
- [x] 用药管理 CRUD (API + 页面)
- [x] 就诊记录 CRUD (API + 页面)
- [x] Wiki + News 模块 (FTS5 搜索)
- [x] **统计报表**: 血糖/血压趋势图 (Chart.js) + CSV 导出
- [x] **数据备份**: SQLite 备份下载/恢复
- [x] **用药提醒**: 今日待服用药物 + 一键打卡
- [x] **心脏指标增强**: 血压分级预警 (WHO) + 心率检测 + 统计分析
- [x] **健康档案汇总**: 个人健康概览 + 评分 + 关键指标
- [x] **统计报表增强**: 分布图 + 周对比 + 时机分析

## 进行中
- [ ] Phase 2 剩余功能

## 未开始
- [ ] Phase 3: 智能分析 (趋势预警)

## 技术栈
- Python 3.14 + FastAPI + SQLAlchemy + Jinja2 + SQLite
- Chart.js 图表
- HTMX 交互
- Tailwind CSS (CDN)

## Git 分支
- main: 生产环境
- hermes/hermes-f2f72f89: 开发分支 (当前)
