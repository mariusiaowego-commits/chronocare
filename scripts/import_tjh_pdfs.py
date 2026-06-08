"""Import tjh's 49 medical PDFs into chronocare DB.

Strategy (per 2026-06-08 user decision):
- 49 MedicalRecord rows (record_type=medical_record), one per PDF
- 41 Visit rows, one per unique visit_date for person_id=2
- MedicalRecord.image_path = relative path to PDF
- MedicalRecord.ocr_text = full PDF text
- MedicalRecord.structured_data = extracted {diagnosis, symptoms, treatment, followup}

Usage:
    uv run python scripts/import_tjh_pdfs.py --dry-run     # parse only, no DB write
    uv run python scripts/import_tjh_pdfs.py              # actually import
    uv run python scripts/import_tjh_pdfs.py --rollback   # undo last import (by tag)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

# Project root (works both as script and module)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PDF_DIR = PROJECT_ROOT / "data" / "tjh-pdfs"
DB_PATH = PROJECT_ROOT / "data" / "chronocare.db"

# Target person (verified 2026-06-08: tjh exists as id=2)
PERSON_ID = 2

# ---------------------------------------------------------------------------
# PDF text extraction
# ---------------------------------------------------------------------------

_DATE_RE = re.compile(r"就诊时间[：:]\s*(\d{4})[-/](\d{1,2})[-/](\d{1,2})")
_HOSPITAL_RE = re.compile(r"(复旦大学附属中山医院[^\n]+|上海市老年医学中心[^\n]+)")
_DEPT_RE = re.compile(r"科室[：:]\s*([^\n]+)")
_DOCTOR_RE = re.compile(r"医生[：:]\s*([^\n]+)")
_DIAG_RE = re.compile(
    r"(?:^|\n)\s*诊\s*断[：:]\s*([^\n]+)", re.MULTILINE
)  # ^ or newline + optional whitespace before 诊 断, to avoid matching 病史段里的「，诊断：」
_COMPLAINT_RE = re.compile(r"(?:病人)?主诉[：:]\s*([^\n]+)")
_TREATMENT_RE = re.compile(r"处\s*理[：:]\s*\n?([^\n]+(?:\n[^\n]+)*?)(?=\n\s*(?:随访|$))", re.MULTILINE)


def extract_pdf_text(pdf_path: Path) -> str:
    """Run pdftotext and return plain text."""
    result = subprocess.run(
        ["pdftotext", str(pdf_path), "-"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode != 0:
        raise RuntimeError(f"pdftotext failed for {pdf_path.name}: {result.stderr}")
    return result.stdout


# ---------------------------------------------------------------------------
# Field extraction
# ---------------------------------------------------------------------------


@dataclass
class ParsedRecord:
    """Structured result of parsing one PDF."""

    pdf_filename: str
    visit_date: date | None
    hospital: str | None
    department: str | None
    doctor: str | None
    diagnosis: str | None
    chief_complaint: str | None
    treatment: str | None
    raw_text: str
    warnings: list[str] = field(default_factory=list)

    def to_db_dict(self) -> dict:
        """Shape for MedicalRecord.create()."""
        return {
            "person_id": PERSON_ID,
            "record_type": "medical_record",
            "visit_date": self.visit_date,
            "hospital": self.hospital,
            "department": self.department,
            "doctor": self.doctor,
            "image_path": f"data/tjh-pdfs/{self.pdf_filename}",
            "ocr_text": self.raw_text,
            "structured_data": {
                "diagnosis": [self.diagnosis] if self.diagnosis else [],
                "symptoms": [self.chief_complaint] if self.chief_complaint else [],
                "treatment": self.treatment or "未提及",
                "followup": "未提及",
            },
            "doctor_orders": None,
            "lab_results": None,
            "notes": None,
        }


def parse_pdf(pdf_path: Path) -> ParsedRecord:
    """Parse one PDF into structured fields. NEVER raises; collects warnings."""
    warnings: list[str] = []
    text = extract_pdf_text(pdf_path)

    # visit_date
    visit_date: date | None = None
    m = _DATE_RE.search(text)
    if m:
        try:
            visit_date = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError as e:
            warnings.append(f"invalid date: {e}")
    else:
        warnings.append("missing visit date")

    # hospital — use first non-empty match
    hospital = None
    m = _HOSPITAL_RE.search(text)
    if m:
        # Strip whitespace; collapse newlines
        hospital = re.sub(r"\s+", "", m.group(1))
    else:
        warnings.append("missing hospital")

    # department
    m = _DEPT_RE.search(text)
    department = m.group(1).strip() if m else None
    if not department:
        warnings.append("missing department")

    # doctor (optional, often missing on these PDFs)
    m = _DOCTOR_RE.search(text)
    doctor = m.group(1).strip() if m else None

    # diagnosis
    m = _DIAG_RE.search(text)
    diagnosis = m.group(1).strip() if m else None
    if not diagnosis:
        warnings.append("missing diagnosis")

    # chief complaint
    m = _COMPLAINT_RE.search(text)
    chief_complaint = m.group(1).strip() if m else None

    # treatment / 处理 — the section after "处 理：" up to "随访"
    m = _TREATMENT_RE.search(text)
    treatment = None
    if m:
        # Clean up: strip prescription lines, keep summary
        treatment = m.group(1).strip()
        # Truncate to first meaningful content
        if len(treatment) > 500:
            treatment = treatment[:500] + "..."

    return ParsedRecord(
        pdf_filename=pdf_path.name,
        visit_date=visit_date,
        hospital=hospital,
        department=department,
        doctor=doctor,
        diagnosis=diagnosis,
        chief_complaint=chief_complaint,
        treatment=treatment,
        raw_text=text,
        warnings=warnings,
    )


# ---------------------------------------------------------------------------
# Dry-run report
# ---------------------------------------------------------------------------


def dry_run() -> list[ParsedRecord]:
    """Parse every PDF and print a structured report. Do NOT touch DB."""
    pdfs = sorted(PDF_DIR.glob("tjh病例-老年医院-*.pdf"))
    if not pdfs:
        sys.exit(f"No PDFs found in {PDF_DIR}")

    print(f"Found {len(pdfs)} PDFs in {PDF_DIR}\n")

    records: list[ParsedRecord] = []
    for pdf in pdfs:
        try:
            r = parse_pdf(pdf)
        except Exception as e:
            print(f"!! PARSE FAIL: {pdf.name}: {e}")
            continue
        records.append(r)

    # Summary
    by_date: dict[date, list[ParsedRecord]] = {}
    for r in records:
        if r.visit_date:
            by_date.setdefault(r.visit_date, []).append(r)

    n_with_date = sum(1 for r in records if r.visit_date)
    n_with_warnings = sum(1 for r in records if r.warnings)
    print(
        f"Parsed: {len(records)}, with date: {n_with_date}, "
        f"unique visit dates: {len(by_date)}, with warnings: {n_with_warnings}\n"
    )

    # Per-PDF table
    print(f"{'PDF':<45} {'Date':<12} {'Dept':<18} {'Warnings'}")
    print("-" * 110)
    for r in records:
        date_str = r.visit_date.isoformat() if r.visit_date else "MISSING"
        dept = (r.department or "MISSING")[:17]
        warns = ",".join(r.warnings) if r.warnings else ""
        print(f"{r.pdf_filename:<45} {date_str:<12} {dept:<18} {warns}")

    # Hospital frequency
    print("\nHospital distribution:")
    from collections import Counter

    hospitals = Counter(r.hospital for r in records if r.hospital)
    for h, c in hospitals.most_common():
        print(f"  {c:3d}  {h}")

    # Department frequency
    print("\nDepartment distribution:")
    depts = Counter(r.department for r in records if r.department)
    for d, c in depts.most_common():
        print(f"  {c:3d}  {d}")

    # Save parsed records to JSON for the import step
    out_path = Path("/tmp/tjh_parsed_records.json")
    serializable = []
    for r in records:
        d = r.to_db_dict()
        d["visit_date"] = d["visit_date"].isoformat() if d["visit_date"] else None
        d["pdf_filename"] = r.pdf_filename
        d["warnings"] = r.warnings
        serializable.append(d)
    out_path.write_text(json.dumps(serializable, ensure_ascii=False, indent=2))
    print(f"\nParsed records saved to {out_path}")

    return records


# ---------------------------------------------------------------------------
# Real import
# ---------------------------------------------------------------------------


async def import_records(records: list[ParsedRecord]) -> None:
    """Write records into chronocare DB. Idempotency: skip if MedicalRecord
    with the same image_path already exists."""
    # Import here so script can be parsed without DB env
    from sqlalchemy import select

    from chronocare.database import async_session_factory
    from chronocare.models.medical_record import MedicalRecord
    from chronocare.models.visit import Visit

    async with async_session_factory() as session:
        # Check existing image_paths to avoid duplicates
        existing = await session.execute(select(MedicalRecord.image_path))
        existing_paths = {p for p in existing.scalars() if p}
        existing_set = set()
        for p in existing_paths:
            existing_set.add(p)
        print(f"Existing MedicalRecord image_paths: {len(existing_paths)}")

        # Pre-existing visits for this person
        existing_visits = await session.execute(
            select(Visit).where(Visit.person_id == PERSON_ID)
        )
        existing_visit_dates = {v.visit_date for v in existing_visits.scalars()}
        print(f"Existing Visit dates for person {PERSON_ID}: {sorted(existing_visit_dates)}")

        # 1) Insert 49 MedicalRecords
        new_mrs: list[MedicalRecord] = []
        skipped = 0
        for r in records:
            img_path = f"data/tjh-pdfs/{r.pdf_filename}"
            if img_path in existing_set:
                skipped += 1
                continue
            if r.visit_date is None:
                print(f"  SKIP (no date): {r.pdf_filename}")
                continue
            d = r.to_db_dict()
            mr = MedicalRecord(**d)
            session.add(mr)
            new_mrs.append(mr)
        print(f"\nMedicalRecords: {len(new_mrs)} new, {skipped} skipped (duplicate)")

        # 2) Determine unique visit dates to create Visit rows
        new_visit_dates = {r.visit_date for r in records if r.visit_date}
        visit_dates_to_create = sorted(new_visit_dates - existing_visit_dates)
        print(f"Visit dates to create: {len(visit_dates_to_create)}")

        # 3) Create Visit rows first (so we can attach MedicalRecord.visit linkage)
        # Strategy: MedicalRecord doesn't have visit_id FK, so just create Visits
        # for the dates. Attachments field on Visit can list PDF paths per day.
        attachments_by_date: dict[date, list[str]] = {}
        for r in records:
            if r.visit_date:
                attachments_by_date.setdefault(r.visit_date, []).append(
                    f"data/tjh-pdfs/{r.pdf_filename}"
                )

        for vd in visit_dates_to_create:
            # Find first record of that day for hospital/dept
            sample = next(r for r in records if r.visit_date == vd)
            visit = Visit(
                person_id=PERSON_ID,
                visit_date=vd,
                hospital=sample.hospital,
                department=sample.department,
                doctor=sample.doctor,
                visit_type="followup",  # most are 复诊
                chief_complaint=sample.chief_complaint,
                diagnosis=sample.diagnosis,
                prescription=sample.treatment,
                doctor_advice=None,
                next_followup_date=None,
                attachments=attachments_by_date.get(vd, []),
            )
            session.add(visit)
        print(f"Visits: {len(visit_dates_to_create)} new")

        # Commit
        await session.commit()
        print("\n✓ Import committed.")
        print(f"  New MedicalRecords: {len(new_mrs)}")
        print(f"  New Visits: {len(visit_dates_to_create)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Import tjh PDFs to chronocare DB")
    parser.add_argument(
        "--dry-run", action="store_true", help="Parse PDFs only, do not write DB"
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Restore chronocare.db from the pre-import backup in data/backups/",
    )
    args = parser.parse_args()

    if args.rollback:
        # Find the most recent pre-tjh-import backup
        backup_dir = PROJECT_ROOT / "data" / "backups"
        backups = sorted(backup_dir.glob("chronocare-pre-tjh-import-*.db"))
        if not backups:
            sys.exit("No pre-tjh-import backup found in data/backups/")
        latest = backups[-1]
        print(f"Restoring {DB_PATH} from {latest}")
        # Use a copy approach: keep the post-import DB around for forensics
        corrupt_path = DB_PATH.with_suffix(".db.corrupted")
        DB_PATH.rename(corrupt_path)
        latest.rename(DB_PATH)
        print(f"Restored. Old DB preserved at {corrupt_path}")
        return

    # Always do dry-run parse first
    records = dry_run()

    if args.dry_run:
        print("\n[DRY-RUN] No DB writes performed.")
        return

    # Confirm before write
    if sys.stdin.isatty():
        ans = input(f"\nAbout to write {len(records)} MedicalRecords + ~41 Visits to {DB_PATH}. Continue? [y/N] ")
        if ans.strip().lower() != "y":
            print("Aborted.")
            return

    asyncio.run(import_records(records))


if __name__ == "__main__":
    main()
