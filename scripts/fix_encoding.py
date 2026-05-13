"""Fix double-encoded UTF-8 data in the database.

Root cause: Some Chinese text was UTF-8 encoded, then mistakenly treated as
Latin-1/ISO-8859-1 and re-encoded as UTF-8, producing mojibake like:
  测试用户 → C3A6 C2B5 C28B ... (double-encoded)

Fix: For each affected text column, decode the stored bytes as Latin-1 to
recover the original UTF-8 bytes, then verify they are valid UTF-8.
"""
import sqlite3
import sys
from pathlib import Path


def fix_double_encoding(conn: sqlite3.Connection, table: str, column: str, pk: str = "id"):
    """Fix double-encoded UTF-8 in a specific table.column."""
    cursor = conn.execute(f"SELECT {pk}, {column} FROM {table} WHERE {column} IS NOT NULL")
    fixed_count = 0
    for row_id, value in cursor.fetchall():
        if not value or not isinstance(value, str):
            continue
        try:
            # Try to detect double-encoding: encode as latin-1, then decode as utf-8
            raw_bytes = value.encode("latin-1")
            decoded = raw_bytes.decode("utf-8")
            if decoded != value:
                conn.execute(
                    f"UPDATE {table} SET {column} = ? WHERE {pk} = ?",
                    (decoded, row_id),
                )
                fixed_count += 1
                print(f"  [{table}.{column}] id={row_id}: '{value}' → '{decoded}'")
        except (UnicodeDecodeError, UnicodeEncodeError):
            # Not double-encoded, skip
            continue
    return fixed_count


def main():
    db_path = Path(__file__).parent.parent / "data" / "chronocare.db"
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        sys.exit(1)

    print(f"Fixing double-encoded UTF-8 in: {db_path}")
    conn = sqlite3.connect(str(db_path))

    total_fixed = 0

    # persons table
    for col in ["name", "emergency_contact", "preferred_hospital", "primary_doctor", "notes"]:
        total_fixed += fix_double_encoding(conn, "persons", col)

    # visits table (no notes column)
    for col in ["hospital", "department", "doctor", "chief_complaint", "diagnosis",
                 "prescription", "doctor_advice"]:
        total_fixed += fix_double_encoding(conn, "visits", col)

    # blood_sugar_records table
    for col in ["notes"]:
        total_fixed += fix_double_encoding(conn, "blood_sugar_records", col)

    # medical_records table
    for col in ["hospital", "department", "doctor", "notes", "ocr_text", "ocr_raw"]:
        try:
            total_fixed += fix_double_encoding(conn, "medical_records", col)
        except sqlite3.OperationalError:
            pass  # column may not exist

    # conditions table
    for col in ["name", "diagnosed_by", "notes"]:
        total_fixed += fix_double_encoding(conn, "conditions", col)

    conn.commit()
    conn.close()

    print(f"\nDone. Fixed {total_fixed} records.")
    if total_fixed == 0:
        print("No double-encoded data found — all data is already correct.")


if __name__ == "__main__":
    main()
