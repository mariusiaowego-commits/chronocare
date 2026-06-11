---
title: Investigation — chronocare 环境隔离 & 数据污染根因
project: chronocare
date:2026-06-10
author: hermes (default profile)
status:调研完成
---

#调研：chronocare 测试数据污染生产 DB 的根因

## TL;DR

chronocare v0.5.0 的 pytest fixture 直接 import 生产 `chronocare.main:app`，**没有任何 DB override**，
导致 `tests/test_report.py` + `tests/test_report_deep.py` 共26 个测试每次运行都会向生产 `data/chronocare.db`
写入"测试报告人物"/"深度验证人物"/"测试人员"以及关联 medical_records。已确认实证：
**今早 (2026-06-1008:21:50)跑过一次 pytest，污染 +8 条 person。**

##1.污染证据（DB 实测）

```sql
SELECT id, name, created_at FROM persons ORDER BY id;
```

实测结果（截至2026-06-10跑测试前）：

| id | name | created_at |状态 |
|-----|--------------|---------------------|----------|
|1 | qian |2026-05-1803:00:45 | ✅真实 |
|2 | tjh |2026-05-2006:23:44 | ✅真实 |
|3-8 | 测试报告人物 |2026-06-0913:19:58 | ❌污染 |
|9-10|深度验证人物 |2026-06-0913:19:58 | ❌污染 |
|11-25| 测试人员 |2026-06-0913:19:58 | ❌污染 |
|26-31| 测试报告人物 |2026-06-1008:21:50 | ❌污染 (今早) |
|32-33|深度验证人物 |2026-06-1008:21:50 | ❌污染 (今早) |
|34-48| 测试人员 |2026-06-1008:21:50 | ❌污染 (今早) |

**总计46 条污染 person**（id3-48），id=1,2 是真实 qjh/tjh。

medical_records 也污染32 条（id=67-98，全部 person_id关联到污染 person）：

```sql
SELECT id, person_id, type, created_at FROM medical_records WHERE person_id >2 LIMIT5;
--67|11|medical_record|2026-06-0913:19:58
--68|12|lab_report|2026-06-0913:19:58
-- ... (32 条)
```

实证 reproduce (2026-06-10跑完后)：

```bash
$ uv run pytest tests/test_report.py tests/test_report_deep.py
==============================26 passed in0.14s ==============================

$ sqlite3 data/chronocare.db "SELECT COUNT(*) FROM persons WHERE name IN ('测试报告人物','深度验证人物','测试人员')"
54 #46 +8 (本次新增)
```

⚠️ **STATUS.md 第117 行写"已删30 条 测试人员 +32 条孤儿 medical_records"，但 DB 显示实际还有46 条 person**。
文档与现实不一致。

##2.根因分析

###2.1 测试 fixture 直接 import 生产 app

`tests/conftest.py` 第6-7 行：

```python
from chronocare.main import app

@pytest.fixture
async def client():
 async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
 yield ac
```

`app`来自 `chronocare/main.py`，其内部 `database.py:engine = create_async_engine(settings.database_url)`，
`config.py` 默认 `database_url = "sqlite+aiosqlite:///./data/chronocare.db"`。

**测试与生产共享同一个 engine、同一个 DB 文件。**

###2.2 report 测试直接调 HTTP API写数据

`tests/test_report.py:11-19`：

```python
@pytest.fixture
async def person_id(client):
 resp = await client.post("/api/persons", json={"name": "测试报告人物", "gender": "M"})
 assert resp.status_code ==201
 return resp.json()["id"]
```

`test_report_deep.py:150`同样模式写"深度验证人物"。`test_services/test_medical_record.py:257`写"测试人员"。

每次跑 pytest =触发 fixture 创建 person →写入生产 DB。

###2.3 没有 cleanup fixture / 没有 test DB override

仓库 grep验证：

```bash
$ grep -rln "TEST_DB\|test_db\|sqlite:///:memory" tests/
(empty)
```

**没有 in-memory override，没有 fixture-level cleanup，没有 conftest 的 autouse reset**。

###2.4端口层面无隔离

```bash
$ lsof -nP -iTCP -sTCP:LISTEN | grep chronocare
Python63571 mt16 ... TCP127.0.0.1:8000 (LISTEN) #唯一进程，无 dev/test split
```

`scripts/`目录没有像 source-monitor `web-8901.sh` 那样的 dev port 管理脚本。

##3.端口冲突调研（本机）

跨项目调研结果：

|端口 |占用方 | 来源 |
|-------|--------------------------------|----------------------------------------|
|5000 | macOS Control Center | 系统 |
|7000 | macOS Control Center | 系统 |
|8000 | chronocare 生产 (uvicorn) | `lsof` + pid63571 |
|8001 | dizical datasette web | `dizical/docs/使用指南.md:122` |
|8765 | dizical kid_app | `dizical/scripts/start-prod.sh` |
|8900 | source-monitor 生产 (uvicorn) | `moni/web/server.py:23` |
|8901 | source-monitor dev/test | `moni/scripts/web-8901.sh` |
|8905 | source-monitor另一个实例 | `lsof` |
|9222 | x-watch Chrome | `x-watch` skill |
|9223 | moni Chrome (Profile7) | `moni/fetch/chrome_daemon.py` |
|9876 | Python (不明) | `lsof` |
|10000 |百度网盘 | netdisk_s |
|11111 | Futu OpenD | `lsof` |

**结论：9000 /9001 都空闲**（用户已确认）。

##4. 用户决策记录（来自决策访谈）

|决策 | 用户答 | 设计含义 |
|------|--------|----------|
|1.隔离架构 | 不同端口 + 测试数据可 copy 生产 | port 分开 + DB 分开 + 测试启动时 copy |
|2. 测试环境建法 | "我决定，简单" | 用最简方案：shell脚本 + pytest fixture override |
|3.严重程度 | P1 | 本周内修，不阻塞其他工作 |
|4. 健康报告26 个测试污染 | (无需决策，纯事实) |26 测试 =26 fixture person，隔离修一次就解决 |
|5.端口 |9000/9001（用户明确） | 与 source-monitor8900/8901 同模式 |
|6. 测试 DB copy模式 |每次 copy，不能写回 |启动测试时 copy → 测试写 → 关掉丢弃 |
|7. 测试数据需求 | production真实数据够 | 不需造 fixture fake data，直接用 qjh+tjh |

##5. 参考案例：source-monitor dev/test split

`~/dev/source-monitor/scripts/web-8901.sh`已有成熟的 dev/test进程管理范式：

```bash
PIDFILE="$REPO_DIR/data/.web-8901.pid" # 与 prod .web.pid区分
PORT=8901

_start() {
 if [ -s "$PIDFILE"] && kill -0 "$(cat "$PIDFILE")"2>/dev/null; then
 echo "Error: already running"
 exit1
 fi
 cd "$REPO_DIR"
 python3 -c "import uvicorn; from X import create_app; uvicorn.run(create_app(), host='127.0.0.1', port=$PORT, log_level='warning')" &
 echo $! > "$PIDFILE"
}
```

⚠️ **moni 的8901 与 prod8900 共用 prod DB** —— 这是 moni 的设计选择，但**不适用于 chronocare**：
moni 是"可视化预览新 UI"场景，chronocare 是"测试数据污染医疗档案"场景。
医疗档案数据的写隔离是硬性需求，moni 的"共用 DB"方案是错误的参照。

##6.风险 &未知

|风险 |严重度 |缓解 |
|------|--------|------|
| 测试 DB copy启动时生产 DB正在被写（race condition） | 中 | copy 用 `.backup` 命令而非直接 cp，SQLite WAL 安全 |
| 测试 uvicorn进程忘记关掉 →占用9001 → 下次跑测试失败 | 低 | PID file + atexit cleanup |
| pytest 在跑时如果 hot-reload uvicorn reload，连接泄漏 | 低 | 测试不走 uvicorn，只走 conftest fixture |
|真实数据被不小心写到9001 测试 DB 然后 commit进来 | 低 |9001 的 DB 在 `data/test/` 子目录，从 git跟踪里排除 |
| 测试 fixture 在 conftest改写后，旧 tests 可能 break | 中 |跑全套67 个测试验证 |

##7. 推荐结论

**v1.0（本周内）：**

1. 新建 `scripts/web-9001.sh` ——启动测试 uvicorn on port9001
 -启动时 `cp data/chronocare.db data/test/chronocare-test.db`
 - `DATABASE_URL` env override指向 test DB
 - PID file: `data/.web-9001.pid`
2.改 `tests/conftest.py` —— fixture override `chronocare.database.engine`
 - 用 tmp目录 + copy DB模式
3. 加 `data/test/` 到 `.gitignore`
4. 加 Makefile目标: `make test-port`, `make test-port-stop`, `make test`
5. 新建 `scripts/cleanup_test_pollution.py` —— 一键清理已存在的46 条污染 person +32 medical_records

**v1.0 不包含**：

- 不改生产端口（保持8000）
- 不动数据库表结构（不分离 prod/test schema）
- 不引入 Docker（用户要"简单"）
- 不动 pytest本身的配置（除 conftest override）

##8.后续可考虑（v2候选）

- pytest 在 GitHub Actions CI跑，CI 用同样的 DB copy模式
- DB migration工具（如 alembic）需要兼容 env override
-多人协作时，多个9001 实例并发 → 用不同 PID 文件名 +端口递增
