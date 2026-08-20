# 260820 handoff — v0.8.0 化验查询 + 原件预览

## 当前版本 / 分支
- 版本: 0.8.0
- 分支: `feat/lab-query-preview`
- 测试: 85 passed

## 本次变更
- 自然语言查询化验指标（数值 + 分析 + 来源 + 预览图）
- PDF/PNG 原件可预览（文件未丢失）
- 列表页已识别状态修复

## 待处理
- [ ] PR merge
- [ ] tjh 门诊病历没有结构化化验，下一轮再抽
- [ ] 人员显示名仍是 qian / tjh
- [ ] 鉴权、备份 restore 校验（6 月审计，未做）

## 关键文件
- `src/chronocare/services/lab_query.py`
- `src/chronocare/services/lab_aliases.py`
- `src/chronocare/services/preview.py`
- `src/chronocare/templates/query/result.html`
- `src/chronocare/routers/pages/query.py`
