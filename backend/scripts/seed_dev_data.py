"""Local-dev only. Idempotent upsert (by eth_address) of sample student rows."""
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
    {
        "eth_address": "0x73c81a7749f57f3f6a966932907236a107522cc4",
        "name": "Fahriddin Hayitov",
        "student_id": "DEV-003",
        "github": "fahriddin",
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
