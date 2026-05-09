"""Insert two sample students for local development.

DO NOT run in production. Idempotent: upserts by eth_address.

The professor will replace these with real addresses from the existing
gradebook before the end-to-end test. Until then:

  - student_active : an address that has solved a few Ethernaut levels
  - student_empty  : the canonical zero-prefix address; expected score 0
"""
from __future__ import annotations

from sqlalchemy.dialects.postgresql import insert

from app.db import SessionLocal
from app.models import Student

SAMPLE_STUDENTS: list[dict[str, str]] = [
    {
        "eth_address": "0x88ad2c8cf498ba7f076537721cae07906135bf93",
        "name": "Sample Student (active)",
        "student_id": "DEV-001",
        "github": "sample-active",
    },
    {
        "eth_address": "0x0000000000000000000000000000000000000001",
        "name": "Sample Student (empty)",
        "student_id": "DEV-002",
        "github": "sample-empty",
    },
]


def main() -> None:
    with SessionLocal() as db:
        for row in SAMPLE_STUDENTS:
            stmt = (
                insert(Student)
                .values(**row)
                .on_conflict_do_update(
                    index_elements=[Student.eth_address],
                    set_={
                        "name": row["name"],
                        "student_id": row["student_id"],
                        "github": row["github"],
                    },
                )
            )
            db.execute(stmt)
        db.commit()
    print(f"Seeded {len(SAMPLE_STUDENTS)} dev students.")


if __name__ == "__main__":
    main()
