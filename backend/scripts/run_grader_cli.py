"""Run the Ethernaut grader against a Sepolia address — bypasses auth and the
submissions table. Reads `assignments.config_json` from the DB (seed first via
`python tasks.py seed-map`) and SEPOLIA_RPC_URL from .env.

Usage: python -m scripts.run_grader_cli 0xYourAddress
"""
from __future__ import annotations

import json
import sys

from sqlalchemy import select

from app.db import SessionLocal
from app.graders import ethernaut
from app.models import Assignment


def main(argv: list[str]) -> int:
    if len(argv) != 2 or not argv[1].startswith("0x") or len(argv[1]) != 42:
        print("usage: python -m scripts.run_grader_cli 0x<40 hex chars>")
        return 2
    address = argv[1]

    with SessionLocal() as db:
        a = db.scalar(select(Assignment).where(Assignment.code == "assignment_2_ethernaut"))
        if a is None:
            print(
                "assignment 'assignment_2_ethernaut' not found in DB. "
                "Run `python tasks.py seed-map` first."
            )
            return 1
        config = a.config_json

    result = ethernaut.run(config, address)
    print(json.dumps({"status": result.status, "score": result.score, **result.details}, indent=2))
    return 0 if result.status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
