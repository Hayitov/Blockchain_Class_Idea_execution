"""Seed (or re-seed) the Ethernaut assignment row's `config_json`.

Source of truth is the OpenZeppelin Ethernaut repository on GitHub. We fetch
two files from the master branch each time this script runs:

  - client/src/gamedata/gamedata.json       (level metadata, including difficulty)
  - client/src/gamedata/deploy.sepolia.json (level address per deployId)

For each Sepolia level we compute:

    score = min(int(difficulty), 5)

The cap exists because the CS423 syllabus defines complexity on a 0-5 scale.
The official Ethernaut difficulty rating goes up to 7; capping keeps the
numbers comparable to other assignments graded by the same rubric.

The result is written into `assignments.config_json` for the row with
code='assignment_2_ethernaut'. The grader reads this at runtime and never
hardcodes scores. To override an individual level's score, edit
`config_json.level_scores` in Postgres directly — DO NOT redeploy.

Idempotent: re-running this updates the same assignment row, refreshing
the level map and the `source.fetched_at` timestamp.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.db import SessionLocal
from app.models import Assignment

GAMEDATA_URL = (
    "https://raw.githubusercontent.com/OpenZeppelin/ethernaut/master/"
    "client/src/gamedata/gamedata.json"
)
DEPLOY_URL = (
    "https://raw.githubusercontent.com/OpenZeppelin/ethernaut/master/"
    "client/src/gamedata/deploy.sepolia.json"
)

ASSIGNMENT_CODE = "assignment_2_ethernaut"
ASSIGNMENT_TITLE = "Assignment 2 — Ethernaut"
ASSIGNMENT_WEIGHT = 10  # points contributed to the course total; tunable in DB

# Conservative lower bound for log scanning. The OZ Ethernaut proxy was deployed
# on Sepolia well after this block, so paginated eth_getLogs from here is safe.
FROM_BLOCK_DEFAULT = 4_000_000

CAP_RULE = "min(int(difficulty), 5)"

THRESHOLDS = {
    "pass": 7,
    "full_marks": 10,
    "max_score": 10,
    "bonus_min_levels": 15,
    "bonus_points": 4,
}


def fetch_json(url: str) -> dict | list:
    r = httpx.get(url, timeout=30.0, follow_redirects=True)
    r.raise_for_status()
    return r.json()


def build_config() -> dict:
    gamedata = fetch_json(GAMEDATA_URL)
    deploy = fetch_json(DEPLOY_URL)

    if not isinstance(gamedata, dict) or "levels" not in gamedata:
        raise RuntimeError("gamedata.json missing 'levels' key — upstream schema changed?")
    if not isinstance(deploy, dict) or "ethernaut" not in deploy:
        raise RuntimeError("deploy.sepolia.json missing 'ethernaut' key — upstream schema changed?")

    proxy_address = deploy["ethernaut"]
    levels = gamedata["levels"]

    level_scores: dict[str, int] = {}
    level_names: dict[str, str] = {}
    skipped: list[str] = []

    for lvl in levels:
        deploy_id = lvl.get("deployId")
        name = lvl.get("name", "?")
        difficulty_raw = lvl.get("difficulty", "0")
        if deploy_id is None or deploy_id not in deploy:
            skipped.append(f"{name} (deployId={deploy_id!r})")
            continue
        addr = deploy[deploy_id].lower()
        score = min(int(difficulty_raw), 5)
        level_scores[addr] = score
        level_names[addr] = name

    config = {
        "proxy_address": proxy_address,
        "from_block": FROM_BLOCK_DEFAULT,
        "level_scores": level_scores,
        "level_names": level_names,
        "thresholds": THRESHOLDS,
        "cap_rule": CAP_RULE,
        "source": {
            "gamedata_url": GAMEDATA_URL,
            "deploy_url": DEPLOY_URL,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "skipped_levels": skipped,
        },
    }
    return config


def main() -> None:
    print(f"Fetching: {GAMEDATA_URL}")
    print(f"Fetching: {DEPLOY_URL}")
    config = build_config()
    print(
        f"Built config: proxy={config['proxy_address']} "
        f"levels={len(config['level_scores'])} "
        f"skipped={len(config['source']['skipped_levels'])}"
    )

    with SessionLocal() as db:
        existing = db.scalar(select(Assignment).where(Assignment.code == ASSIGNMENT_CODE))
        if existing is None:
            stmt = insert(Assignment).values(
                code=ASSIGNMENT_CODE,
                title=ASSIGNMENT_TITLE,
                weight=ASSIGNMENT_WEIGHT,
                config_json=config,
            )
            db.execute(stmt)
            print(f"Inserted assignment '{ASSIGNMENT_CODE}'.")
        else:
            existing.config_json = config
            print(f"Updated assignment '{ASSIGNMENT_CODE}' (id={existing.id}).")
        db.commit()

    print("Done. Sample of level_scores:")
    sample = list(config["level_scores"].items())[:5]
    print(json.dumps(sample, indent=2))


if __name__ == "__main__":
    main()
