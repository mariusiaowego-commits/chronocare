# ChronoCare 260608 Handoff

> Date: 2026-06-08
> Branch: `feature/tjh-import-49-pdfs` (from `main` @ `5a93976`)
> Tag: `pre-tjh-import` (DB state marker)

## 本次 session 目标
导入 tjh 在上海市老年医学中心 2024-03-13 → 2026-05-27 期间的 49 张就诊记录 PDF。

## 完成的变更

### 1. 数据导入（49 MedicalRecord + 41 Visit）
- **方案**: 全保留（用户选）— 每个 PDF 1 条 MedicalRecord（image_path = PDF 相对路径），每个 visit_date 1 条 Visit（attachments 列出当日所有 PDF）
- **person_id**: 2 (tjh, 已存在)
- **关键字段提取** (pdftotext + 正则):
  - `visit_date` ← `就诊时间：YYYY-MM-DD`
  - `hospital` ← `复旦大学附属中山医院[梅陇/闵行]院区`
  - `department` ← `科室：xxx`
  - `diagnosis` ← `诊 断：xxx` (修复了原 regex 会误抓「现病史」段里旧检查报告引用的 bug)
  - `chief_complaint` ← `主诉：xxx`
  - `treatment` ← `处 理：xxx...` (含处方/检查/医嘱)
- **dry-run**: 49/49 全部解析成功，0 警告
- **最终**: 49 MR + 41 Visit 写入 `data/chronocare.db`

### 2. Schema 修复（顺手）
- `src/chronocare/schemas/visit.py` 中 `VisitBase.attachments` 和 `VisitUpdate.attachments` 从 `dict | None` 改为 `list[str] | None`
- 原因: 真实数据（Visit.attachments）是 JSON array，但 schema 限制为 dict，导致 `/api/visits` 返 500
- Visit 1 (qian) attachments=None 没触发 bug；我们的 import 让 bug 首次显现

### 3. 新增 import 脚本
- `scripts/import_tjh_pdfs.py`:
  - `--dry-run`: 解析 PDF 不写库
  - 默认: 写库
  - `--rollback`: 还原到 `data/backups/` 里的最新 pre-tjh-import 备份
  - 幂等: 跳过同 image_path 的 MR

## 关键文件
| 文件 | 状态 | 说明 |
|------|------|------|
| `data/tjh-pdfs/*.pdf` | 49 files | tjh 就诊记录原 PDF，git ignore |
| `data/backups/chronocare-pre-tjh-import-20260608-171018.db` | 106KB | DB 回退源 1 |
| `/tmp/chronocare-pre-tjh-import.db` | 106KB | DB 回退源 2 (备份) |
| `scripts/import_tjh_pdfs.py` | new | 导入 + dry-run + rollback |
| `src/chronocare/schemas/visit.py` | M | attachments dict → list[str] |
| `vibe-coding-log/2026-06-08.md` | new | 今日开发日志 |

## DB 状态
- 导入前: 2 persons (qian, tjh), 1 visit, 17 medical_records
- 导入后: 2 persons, 42 visits, 66 medical_records

## 回退步骤（如果需要）
```bash
# 1. 回退代码
git checkout main
git branch -D feature/tjh-import-49-pdfs

# 2. 回退 DB（任选其一）
uv run python scripts/import_tjh_pdfs.py --rollback
# 或手动：
cp data/backups/chronocare-pre-tjh-import-20260608-171018.db data/chronocare.db
```

## 验证清单
- [x] DB 写入计数: 49 MR + 41 Visit
- [x] 重复检查: 同 image_path 不会重复（脚本幂等）
- [x] API: `/api/medical-records/18` 返回完整 JSON
- [x] API: `/api/visits?person_id=2` 返回 41 条 + 正确 attachments
- [x] Lint: ruff check 通过
- [x] Smoke: 2/2 tests passed
- [ ] 浏览器手动验证 (留给用户)

## 待处理（out of scope for this session）
- [ ] `main.py` mount `data/tjh-pdfs/` 让 PDF 可直接 URL 访问
- [ ] 业务复核 `visit_type` (目前全 `followup` 推断)
- [ ] 处理 `chief_complaint` 里残留的 `{emr_reference:诊断.诊断}` (HIS 模板变量)
- [ ] 5 个 `scripts/download_*.py` 决定保留/丢弃
- [ ] 把 `feature/tjh-import-49-pdfs` 推到 remote + PR (按用户原话「分支上开发-提pr-review-合到主版本」)

## 端口规则（记忆更新）
- 8765 = dizical kid-app (dizical 主服务 worktree 保留端口)
- 8766 = dizical worktree
- 8000 = chronocare (现有长跑 uvicorn, --reload 模式)
- 8900 = moni 生产
- 8901 = moni dev-test
- chronocare 本次验证直接用现有 8000，未启新服务
