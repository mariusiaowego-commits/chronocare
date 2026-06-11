# 260611-handoff.md

> 生成时间: 2026-06-11
> 当前版本: v0.5.0 → v0.6.0 (test isolation)
> 分支: main (commit 4334325, PR #5 merged)

## 本次 Session 变更摘要

### 1. 测试隔离 (v0.6.0 核心改动)

**问题**: pytest 直接 import 生产 app，没有 DB override，每次 `uv run pytest` 向生产 `data/chronocare.db` 写入测试数据。

**实证**:
- 123 条污染 person (name='测试报告人物'/'深度验证人物'/'测试人员')
- 80 条污染 medical_records (全部 person_id 关联到污染 person)
- 今早 (2026-06-10) Alma agent 跑了一次 pytest，污染 +8 条

**根因**: `tests/conftest.py` 直接 `from chronocare.main import app`，app 内部的 engine 指向生产 DB。

**方案**: session-scoped monkeypatch:
- 从生产 DB 用 SQLite `.backup()` 拷贝到 tmp 目录
- monkeypatch `chronocare.database.engine` + `async_session_factory` 指向 tmp
- 生产 `database.py` 零改动，uvicorn :8000 不受影响
- pytest 结束后 tmp 自动清理

**验证**: 67/67 tests pass + 测试后生产 DB 零污染。

### 2. 生产 DB 清理

- `scripts/cleanup_test_pollution.py` 一次性清理脚本
- 已执行: 删除 123 person + 80 medical_records
- 备份: `data/backups/chronocare-pre-cleanup-20260611-085928.db`
- 清理后: 2 个真实 person (qian, tjh) + 66 条真实 medical_records

### 3. Alma agent 调研 (2026-06-10, default profile)

- commit bc886ce: `prd/env-isolation-prd-v1.md` (631行) + `research/env-isolation-investigation-2026-06-10.md` (209行)
- 作者: yoyoba@alma.com (Alma agent, default profile session)
- 内容: 完整的根因分析 + 实施 PRD
- 未动业务代码，纯文档

### 4. 测试修复

- `test_list_person_reports`: 从绝对计数断言改为相对断言（DB copy 可能包含已有数据）

## Git 工作流

- 分支: `feat/test-isolation` → PR → main
- commit 3989999: 4 files changed, +220 -4
- PR 待创建（安全策略拦截，需手动）

## 关键文件

| 文件 | 说明 |
|------|------|
| `tests/conftest.py` | 核心：session-scoped `_isolated_engine` fixture |
| `tests/test_report.py` | 修复绝对计数断言 |
| `scripts/cleanup_test_pollution.py` | 一次性清理脚本（已执行） |
| `.gitignore` | 新增 data/test/ + .web-9001.pid |
| `prd/env-isolation-prd-v1.md` | Alma 调研 PRD |
| `research/env-isolation-investigation-2026-06-10.md` | Alma 调研报告 |

## 待处理事项

- [x] PR #5 合并到 main (2026-06-11, commit 4334325)
- [x] main 上 pytest 确认无回归 (67/67 pass, 零污染)
- [x] feat/test-isolation 分支已删除 (local + remote)
- [x] PR 合并后在 main 上跑一次 pytest 确认无回归
- [ ] `scripts/cleanup_test_pollution.py` 可标记为已执行（后续不再需要）
- [ ] 后续所有测试都应使用 conftest.py 的隔离 engine，不要再直接 import 生产 app

## 技术决策

1. **monkeypatch vs env-override**: 选 monkeypatch — database.py 不改动，diff 更小
2. **session-scoped vs function-scoped**: 选 session — 一个 pytest run 只 swap 一次
3. **SQLite .backup() vs shutil.copy**: 选 .backup — SQLite 原生备份，一致性更好
4. **tmp DB vs test DB 文件**: 选 tmp — pytest 原生 tmp_path_factory，自动清理
