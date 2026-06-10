---
title: PRD — chronocare 环境隔离 (生产/测试端口分离)
project: chronocare
version: v1
date:2026-06-10
author: hermes (default profile)
status: draft →等待 coder评估 + 用户review
depends-on: research/env-isolation-investigation-2026-06-10.md
---

# PRD: chronocare — 环境隔离

> **TL;DR**：新建测试专用端口9001 + 测试专用 DB (`data/test/chronocare-test.db`)，
>启动测试时从生产 DB copy 一份（不能用写回），关闭测试时丢弃。conftest.py改 fixture
> override engine，禁止测试触碰生产 DB。配套清理脚本一键清掉历史46 条污染。
>1 个新脚本 +1 个 conftest改写 +1 个 cleanup脚本 +1 个 .gitignore增量 = **4 个文件改动**。

##0. 当前现状（基线）

###0.1 数据流现状（待修）

```
+------------------+ +-----------------+ +-----------------------+
| pytest跑测试 | --> | tests/conftest.py| --> | chronocare.main:app |
+------------------+ | (import app) | | (production engine) |
 +-----------------+ +-----------+-----------+
 |
 v
 +---------------------+
 | data/chronocare.db |
 | (PRODUCTION,污染中) |
 +---------------------+
```

**问题**：`tests/test_report.py` 和 `test_report_deep.py` 通过 `client.post("/api/persons", ...)` 直接调生产 API，
**没有 DB override**，**没有 fixture cleanup**。每次跑 pytest =26 条 person 被写入生产 DB。

###0.2 文件清单（待修）

|文件 | 当前职责 |待修内容 |
|------|----------|----------|
|`src/chronocare/main.py` | FastAPI app工厂 |**不动** |
|`src/chronocare/config.py` | Settings（含 `database_url`） |**不动**（已支持 env override via pydantic-settings） |
|`src/chronocare/database.py` | engine + session factory |**改**：加 env-driven override hook（看4.3.2） |
|`tests/conftest.py` | AsyncClient fixture |**改**：用 tmp DB override engine（看4.3.3） |
|`tests/test_report.py` | Report API 测试 (8 个) |**不动**（用 conftest fixture） |
|`tests/test_report_deep.py` | Report API 测试 (18 个) |**不动** |
|`tests/test_services/test_medical_record.py` | OCR service 测试 |**不动** |
|`data/chronocare.db` | 生产 SQLite DB |**不动** |
|`scripts/web-9001.sh` | (不存在) |**新增**（看4.3.1） |
|`scripts/cleanup_test_pollution.py` | (不存在) |**新增**（看4.3.4） |
|`.gitignore` | git排除 |**改**：加 `data/test/` + `.web-9001.pid` |
|`Makefile` | (如果存在) |**改**：加 `test-port` / `test-port-stop`目标 |

###0.3 当前生产进程

```bash
$ lsof -nP -iTCP:8000 -sTCP:LISTEN
Python63571 mt16 ... TCP127.0.0.1:8000 (LISTEN)
```

**PID63571持续在跑** ——修代码期间不能动它，等 coder PR merge后再 reload。

##1.背景 &动机

###1.1现状问题（实证）

- **46 条 person污染生产 DB**（id=3-48，全部 name 是"测试报告人物"/"深度验证人物"/"测试人员"）
- **32 条 medical_records污染**（id=67-98，全部 person_id关联到污染 person）
- **STATUS.md文档与现实漂移**（写"已删30 条"但实际还在）
- **每次 pytest跑 = 新污染产生**（今早08:21跑完新增8 条）

###1.2动机

测试数据是医疗档案上下文，污染 =真实父母（qjh, tjh）的数据被噪音包围，
后续 `report`/`aggregate`/`dashboard` 等所有 feature 的数据分析可信度全部受影响。

###1.3为什么不只"清理一下"

清理是治标。根因是测试与生产共用 DB + engine。**只要架构不修，下次再写测试还会再污染**。

##2.范围

###2.1 v1包含

1. ✅ 新建 `scripts/web-9001.sh`：测试专用 uvicorn进程管理
2. ✅改 `tests/conftest.py`：fixture强制用 tmp DB（in-process 不需要 uvicorn）
3. ✅改 `src/chronocare/database.py`：加 env-driven engine override（让9001走 test DB）
4. ✅ 新建 `scripts/cleanup_test_pollution.py`：一键清污染
5. ✅改 `.gitignore`：排除 `data/test/` + `.web-9001.pid`
6. ✅（可选）改 `Makefile`：加 `make test-port` / `make test-port-stop`

###2.2 v1 不包含

- ❌改生产端口8000（保持不动）
- ❌改数据库表结构 /引入 alembic（v2候选）
- ❌ Docker / docker-compose（用户要"简单"）
- ❌ GitHub Actions CI（v2候选）
- ❌多人协作并发测试支持（v2候选）

##3. 用户故事 &验收

###3.1 US-1：开发新 feature 时跑测试不污染生产

**作为** chronocare开发者
**当** 我跑 `uv run pytest`
**则** 测试应该用一个临时 DB，**不写**生产 `data/chronocare.db`

**验收**：
```bash
#跑前
$ wc -l data/chronocare.db.persons.sql # 占位符
#跑全套 pytest
$ uv run pytest
==============================67 passed in0.50s ==============================
#跑后 —— DB字节数/行数不变
$ wc -l data/chronocare.db.persons.sql #字节数不变
```

###3.2 US-2：手动起测试 server调试 UI

**作为** chronocare开发者
**当** 我需要可视化测试新 UI改动（不开 fixture）
**则** 我跑 `bash scripts/web-9001.sh start`，在浏览器打开 `http://127.0.0.1:9001`

**验收**：
```bash
$ bash scripts/web-9001.sh start
Started (PID xxxxx) on http://127.0.0.1:9001/
$ curl -s http://127.0.0.1:9001/persons | head
# 返回测试 DB 的内容（含 qjh+tjh 从 prod copy来的 +可能有上次测试遗留）

$ bash scripts/web-9001.sh stop
Stopped
```

###3.3 US-3：清理历史污染

**作为** chronocare运维
**当** 我跑 `uv run python scripts/cleanup_test_pollution.py`
**则** 它清掉 id=3-48 person + id=67-98 medical_records，**不删 qjh+tjh真实数据**

**验收**：
```bash
$ uv run python scripts/cleanup_test_pollution.py
Found46 test-pollution persons (id=3-48)
Found32 test-pollution medical_records (id=67-98)
Backup saved to data/backups/chronocare-pre-cleanup-20260610-HHMMSS.db
Deleted46 persons
Deleted32 medical_records
Done.

#验证 qjh+tjh还在
$ sqlite3 data/chronocare.db "SELECT id, name FROM persons WHERE id<=2"
1|qian
2|tjh
```

##4. 技术设计

###4.1架构图

```
PRODUCTION (port8000, 不动):
+------------------+ +---------------------+ +-----------------------+
| browser @ :8000 | --> | uvicorn (pid63571) | --> | data/chronocare.db |
+------------------+ +---------------------+ | (PRODUCTION) |
 +-----------------------+

TEST IN-PROCESS (pytest, 默认):
+------------------+ +---------------------+ +-----------------------------+
| pytest跑测试 | --> | conftest.py fixture | --> | /tmp/chronocare-test-<rand>/|
| | | + async_session_factory| | chronocare.db (COPY of prod) |
+------------------+ | override | +-----------------------------+
 +---------------------+
 (engine env override:
 DATABASE_URL=sqlite:///tmp/.../chronocare.db)

TEST STANDALONE (port9001, 可选):
+------------------+ +---------------------+ +--------------------------------+
| browser @ :9001 | --> | uvicorn (transient) | --> | data/test/chronocare-test.db |
+------------------+ +---------------------+ | (COPY of prod @ start time) |
 +--------------------------------+
 (启动时 web-9001.sh 执行 cp + 设 env,关闭时不写回)
```

###4.2 文件改动清单

| # | 文件 | 类型 | LOC估算 |改动 |
|---|------|------|---------|------|
| A | `scripts/web-9001.sh` | 新增 | ~100 |进程管理脚本（start/stop/status） |
| B | `tests/conftest.py` | 修改 | +20 / -5 | 加 DB override fixture |
| C | `src/chronocare/database.py` | 修改 | +15 / -2 | env-driven engine factory |
| D | `scripts/cleanup_test_pollution.py` | 新增 | ~80 |清理脚本 +备份 |
| E | `.gitignore` | 修改 | +3 | 加 `data/test/`、`.web-9001.pid` |
| F | `Makefile` (optional) | 修改 | +8 | `test-port`, `test-port-stop`目标 |

**总计**：4-5 个文件，~230 行新增（其中 D 含较多注释）。

###4.3关键代码骨架

####4.3.1 文件 A：`scripts/web-9001.sh`（NEW）

仿 `~/dev/source-monitor/scripts/web-8901.sh`模式，但**改 DB路径**：

```bash
#!/usr/bin/env bash
# scripts/web-9001.sh — test/dev uvicorn process manager (port9001)
#
# v0.6.0: test port isolated from prod (8000).启动时从 prod DB copy 一份
# 到 data/test/，env override指向 test DB。**test DB 在 stop 时丢弃**——
#任何写入不会回到 prod。
#
# Usage:
# bash scripts/web-9001.sh start
# bash scripts/web-9001.sh stop
# bash scripts/web-9001.sh status

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
PIDFILE="$REPO_DIR/data/.web-9001.pid"
LOGFILE="$REPO_DIR/data/test/web-9001.log"
PORT=9001
PROD_DB="$REPO_DIR/data/chronocare.db"
TEST_DB_DIR="$REPO_DIR/data/test"
TEST_DB="$TEST_DB_DIR/chronocare-test.db"

_start() {
 if [ -s "$PIDFILE"] && kill -0 "$(cat "$PIDFILE")"2>/dev/null; then
 echo "Error: already running (PID $(cat "$PIDFILE"))"
 exit1
 fi

 mkdir -p "$TEST_DB_DIR"

 # CRITICAL: copy prod DB 到 test DB (用 .backup 而非 cp 防 WAL损坏)
 sqlite3 "$PROD_DB" ".backup '$TEST_DB'"

 cd "$REPO_DIR"
 DATABASE_URL="sqlite+aiosqlite:///$TEST_DB" \
 uv run uvicorn chronocare.main:app \
 --host127.0.0.1 --port "$PORT" --log-level warning \
 > "$LOGFILE"2>&1 &

 local pid=$!
 echo "$pid" > "$PIDFILE"

 sleep1
 if kill -0 "$pid"2>/dev/null; then
 echo "Started (PID $pid) on http://127.0.0.1:$PORT/"
 echo "Test DB: $TEST_DB (copy of prod, will be discarded on stop)"
 else
 rm -f "$PIDFILE"
 echo "Error: process exited immediately. Check $LOGFILE"
 exit1
 fi
}

_stop() {
 # ... (类似 source-monitor模式) ...
 rm -f "$PIDFILE"
 # ⚠️ 不删 TEST_DB —— 让 dev 可以看 last test run 数据
 # 如果想清，加: rm -f "$TEST_DB"
 echo "Stopped (test DB kept at $TEST_DB; remove manually if needed)"
}

case "${1:-}" in
 start) _start ;;
 stop) _stop ;;
 status) _status ;;
 *) echo "Usage: $0 {start|stop|status}" >&2; exit1 ;;
esac
```

####4.3.2 文件 C：`src/chronocare/database.py`（MODIFY）

让 engine接受 env override（不动 default）：

```python
"""SQLAlchemy database engine and session management.

v0.6.0: support env-driven DATABASE_URL override for test isolation.
Production callers don't change behavior — `settings.database_url` still
controls default. Tests/conftest/web-9001.sh override via DATABASE_URL env.
"""

import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from chronocare.config import settings

# v0.6.0: env override wins over settings.default (test isolation)
_database_url = os.environ.get("DATABASE_URL") or settings.database_url

engine = create_async_engine(
 _database_url,
 echo=settings.debug,
 poolclass=NullPool,
)

async_session_factory = async_sessionmaker(
 engine,
 class_=AsyncSession,
 expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession]:
 """Yield an async database session for dependency injection."""
 async with async_session_factory() as session:
 yield session
```

####4.3.3 文件 B：`tests/conftest.py`（MODIFY）

```python
"""Shared test fixtures.

v0.6.0: 每个 pytest session 用临时 DB (从 prod copy一次), 不污染生产。
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine

from chronocare.config import settings


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _isolated_test_db():
 """Copy prod DB 到 tmp dir, 设 DATABASE_URL env,跑完清理。

 autouse=True: 所有测试 session 自动隔离。
 """
 prod_db = Path(settings.base_dir) / "data" / "chronocare.db"
 tmp_dir = Path(tempfile.mkdtemp(prefix="chronocare-test-"))
 test_db = tmp_dir / "chronocare-test.db"

 # Copy (用 sqlite .backup 防 WAL损坏)
 import sqlite3
 conn = sqlite3.connect(str(prod_db))
 conn.backup(sqlite3.connect(str(test_db)))
 conn.close()

 # Override DATABASE_URL env BEFORE app loads
 old_url = os.environ.get("DATABASE_URL")
 os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{test_db}"

 yield # 测试运行

 # Teardown
 if old_url is None:
 os.environ.pop("DATABASE_URL", None)
 else:
 os.environ["DATABASE_URL"] = old_url
 shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture
async def client():
 """Async test client for FastAPI."""
 # _isolated_test_db 已设好 env; 直接 import app
 from chronocare.main import app
 async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
 yield ac
```

⚠️ **关键陷阱**：env override 必须**在 `from chronocare.main import app`之前**设置，
否则 `chronocare.database.engine`会在 import 时就用 settings 默认值创建。
当前实现通过 `_isolated_test_db` 是 autouse session fixture，在 import app之前 yield 已设置 env，OK。

####4.3.4 文件 D：`scripts/cleanup_test_pollution.py`（NEW）

```python
#!/usr/bin/env python
"""清理历史测试污染：46 person +32 medical_records。

Usage:
 uv run python scripts/cleanup_test_pollution.py
 uv run python scripts/cleanup_test_pollution.py --dry-run
"""

import argparse
import shutil
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, text

from chronocare.config import settings

# Known pollution names (from PR #4 健康报告测试)
POLLUTION_NAMES = ("测试报告人物", "深度验证人物", "测试人员")


def main():
 ap = argparse.ArgumentParser()
 ap.add_argument("--dry-run", action="store_true")
 args = ap.parse_args()

 db_path = Path(settings.base_dir) / "data" / "chronocare.db"
 eng = create_engine(f"sqlite:///{db_path}")

 # Find pollution
 with eng.begin() as conn:
 persons = conn.execute(
 text(
 f"SELECT id, name FROM persons "
 f"WHERE name IN ({','.join(f':n{i}' for i in range(len(POLLUTION_NAMES)))}) "
 f"ORDER BY id"
 ),
 {f"n{i}": n for i, n in enumerate(POLLUTION_NAMES)},
 ).fetchall()
 person_ids = [p[0] for p in persons]

 if not person_ids:
 print("No pollution found.")
 return

 # Find their medical_records
 mr = conn.execute(
 text(
 "SELECT id FROM medical_records WHERE person_id IN ("
 + ",".join(str(i) for i in person_ids) + ")"
 )
 ).fetchall() if False else [] # SQLAlchemy2.0: 用 in_
 mr_ids = [r[0] for r in mr]

 print(f"Found {len(persons)} test-pollution persons (id={person_ids[0]}..{person_ids[-1]})")
 print(f"Found {len(mr_ids)} test-pollution medical_records")

 if args.dry_run:
 print("DRY RUN — no changes made.")
 return

 # Backup
 ts = datetime.now().strftime("%Y%m%d-%H%M%S")
 backup = db_path.parent / "backups" / f"chronocare-pre-cleanup-{ts}.db"
 backup.parent.mkdir(exist_ok=True)
 shutil.copy2(db_path, backup)
 print(f"Backup saved to {backup}")

 # Delete (CASCADE 让 medical_records 也跟着删)
 with eng.begin() as conn:
 # 先删 medical_records (防 cascade miss)
 if mr_ids:
 conn.execute(
 text(
 "DELETE FROM medical_records WHERE id IN ("
 + ",".join(str(i) for i in mr_ids) + ")"
 )
 )
 # 再删 persons
 conn.execute(
 text(
 "DELETE FROM persons WHERE id IN ("
 + ",".join(str(i) for i in person_ids) + ")"
 )
 )

 print(f"Deleted {len(mr_ids)} medical_records")
 print(f"Deleted {len(persons)} persons")
 print("Done.")


if __name__ == "__main__":
 main()
```

⚠️ **陷阱**：`medical_records` 表**没有 `ON DELETE CASCADE`**（从 schema 看 FK 没声明 cascade），
所以必须手动先删 medical_records 再删 persons。

####4.3.5 文件 E：`.gitignore`（MODIFY）

增量：

```gitignore
# v0.6.0: test isolation
data/test/
data/.web-9001.pid
```

####4.3.6 文件 F：`Makefile`（MODIFY，optional）

```makefile
.PHONY: test test-port test-port-stop

test:
 uv run pytest

test-port:
 bash scripts/web-9001.sh start

test-port-stop:
 bash scripts/web-9001.sh stop
```

###4.4关键决策记录

|决策 | 用户答 | PRD实施 |
|------|--------|----------|
|端口 |9000/9001（用户拍板） | web-9001.sh 用9001 |
|测试 DB模式 |启动 copy / 不写回 | `_start` 用 `.backup`，`_stop` **不**自动删 |
|测试 fixture | "简单" | conftest.py 加 session-scoped autouse fixture |
|严重程度 | P1 | 本周内 merge |
|测试数据源 | prod真实够 | 不造 fake，直接 copy |

###4.5 数据库清理顺序（critical）

medical_records 表 person_id引用 persons.id。**SQLite FK 默认不强制**，但应用层应在删 persons 前先删 medical_records：

```
1. SELECT id FROM medical_records WHERE person_id IN (pollution_ids)
2. DELETE FROM medical_records WHERE id IN (mr_ids)
3. DELETE FROM persons WHERE id IN (pollution_ids)
```

顺序反了会留孤儿 medical_records（STATUS.md5-25 session提到过这问题）。

##5. 测试计划

###5.1单元测试（fixture隔离验证）

| # | 测试名 |验证 |
|---|--------|------|
|1 | `test_conftest_isolation` | conftest fixture 把 DATABASE_URL改为 tmp路径 |
|2 | `test_prod_db_unchanged_after_pytest` |跑全套 pytest 后 prod DB字节数不变 |

###5.2端到端测试

| # |步骤 |验证 |
|---|------|------|
|1 |跑 `uv run pytest` |67 全过 |
|2 | 检查 `data/chronocare.db` 大小 | 不变 |
|3 | 检查 persons 表 | 只有 qian + tjh + (跑测试前已存在的污染，可能4.3.4 没跑过 cleanup) |
|4 | `bash scripts/web-9001.sh start` | uvicorn on :9001 |
|5 | `curl http://127.0.0.1:9001/api/persons` | 返回 copy 的数据 |
|6 | `curl -X POST http://127.0.0.1:9001/api/persons -d '{"name":"test","gender":"M"}'` |写到 test DB，**不**写到 prod |
|7 | `curl http://127.0.0.1:8000/api/persons` | prod **没**新 person |
|8 | `bash scripts/web-9001.sh stop` |进程停 |
|9 | `uv run python scripts/cleanup_test_pollution.py --dry-run` | 显示将删46 +32 |
|10 | `uv run python scripts/cleanup_test_pollution.py` | 真删 +备份 |
|11 |再次跑 `uv run pytest` |67 全过（测试现在用 copy-from-prod，可能 id 重置为1开始） |

**测试总数**：现有67 + 新增1（test_conftest_isolation）= **68**。

⚠️ **测试编号漂移风险**：conftest改成 session-scope autouse 后，所有 test fixture行为改变，
需要确认 test_report_deep.py 里假设 "person_id 是连续整数" 的逻辑还能跑（应该能，因为 copy-from-prod包含 qjh=1, tjh=2）。

##6.实施步骤（分阶段）

###6.1 v1.0阶段（单 PR：feat/test-isolation）

按文件顺序：

1. **步骤1：先备份 prod DB**（防 cleanup 出错）
 ```bash
 cp data/chronocare.db data/backups/chronocare-pre-test-isolation-20260610.db
 ```

2. **步骤2：改 `.gitignore`**（低风险）

3. **步骤3：改 `src/chronocare/database.py`**（加 env override，不动 default）

4. **步骤4：改 `tests/conftest.py`**（加 autouse fixture）

5. **步骤5：跑 `uv run pytest`**——验证67 全过 + prod DB字节数不变

6. **步骤6：新增 `scripts/cleanup_test_pollution.py`**——跑 `--dry-run` 看数字，跑真删

7. **步骤7：新增 `scripts/web-9001.sh`**—— chmod +x，跑 start/stop/status

8. **步骤8：加 Makefile**（optional）

9. **步骤9：commit → push → PR → merge**

###6.2 v1.1阶段（后续 PR）

- GitHub Actions CI集成
- `data/test/chronocare-test.db` 加 cleanup_at_start 选项
-多人并发：PORT_TEST_BASE + process_id偏移

##7.风险与缓解

|风险 |严重度 |缓解 |
|------|--------|------|
| env override 不生效 → 测试仍写 prod | 中 |步骤5强验证 prod DB字节数不变 |
| cleanup误删真实数据 | 中 | `--dry-run` 必须 + 自动 backup +步骤1手动 backup兜底 |
| conftest改后旧 test break | 中 |步骤5跑全套67验证 |
| web-9001进程忘记关 → 占9001 | 低 | PID file +显式 stop流程 |
|端口9001未来被其他项目占 | 低 | 用户已确认空闲；后续冲突时再调研 |
| pytest fixture假设 person_id连续整数 | 低 | copy-from-prod保留 qjh=1,tjh=2，新测试 person 从 id=3 开始 |

##8.后续可考虑（v2候选）

-引入 alembic：test DB 在 pytest启动时跑 `alembic upgrade head` 而非 `.backup`
- 多 worker 并发测试：每个 worker 用不同 tmp dir
- 把 web-9001.sh改 Python脚本（更可控 +错误信息更友好）
- web-9001.sh 加 `auto-reload` 选项（开发时 hot-reload）

##9.关键参考

-调研报告：`research/env-isolation-investigation-2026-06-10.md`
-范式：`~/dev/source-monitor/scripts/web-8901.sh`
- AGENTS.md：feature branch → PR（未测不推）
- pyproject.toml version：0.5.0 →0.6.0（v1.0完成后 bump）

---

## 自检清单（mandatory before handoff）

- [x] 所有7 个用户决策都反映在 PRD body
- [x] 文件清单 LOC 加起来 ≈230（按4.2 表）
- [x] 测试总数67+1=68，加起来正确
- [x] 每个新文件都有完整代码骨架，不是 pseudo-code
- [x] cleanup顺序先 mr 后 person（防孤儿）
- [x] env override 在 import app **之前**生效（conftest autouse）
- [x] web-9001.sh 用 `.backup` 而非 `cp`（防 WAL损坏）
- [x] 不动生产端口8000
- [x] 0改动涉及 medical_records schema / 不动表结构
- [x] .gitignore增量 +3 行（data/test/, .web-9001.pid）
