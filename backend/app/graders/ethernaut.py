"""Ethernaut grader.

Reads everything that varies — proxy address, from-block lower bound, the
level address -> score map, the syllabus thresholds — from
`assignments.config_json`. Hard-codes nothing about scoring. The professor
overrides scores by editing config_json in Postgres; no redeploy needed.

Algorithm:
  1. Compute topic0 = keccak256("LevelCompletedLog(address,address,address)").
  2. Build topic1 = 32-byte left-padded player address.
  3. Paginate eth_getLogs in CHUNK_BLOCKS-block windows from config.from_block
     up to current head, filtering [topic0, topic1, null, null] on the proxy.
  4. For each matching log, take topic[3] (the level contract), look up the
     score in config.level_scores (lowercased keys). Dedupe by level address.
  5. raw_score = sum of level scores; capped = min(max_score, raw_score).
     bonus = bonus_points if distinct_levels >= bonus_min_levels else 0.
     total = capped + bonus. Final score is what we persist.

Any RPC / decoding error returns GraderResult(status="error", ...). The
route layer persists the error as an append-only grader_runs row — runs are
never silently dropped.
"""
from __future__ import annotations

import time
from typing import Any

from web3 import Web3
from web3.exceptions import Web3Exception

from app.graders.base import GraderResult
from app.web3_client import get_web3

EVENT_SIGNATURE = "LevelCompletedLog(address,address,address)"
CHUNK_BLOCKS = 50_000
DEFAULT_MAX_SCORE = 10
DEFAULT_BONUS_POINTS = 4
DEFAULT_BONUS_MIN_LEVELS = 15


def _topic0() -> str:
    return Web3.keccak(text=EVENT_SIGNATURE).to_0x_hex()


def _player_topic(address: str) -> str:
    addr = address.lower().removeprefix("0x")
    if len(addr) != 40:
        raise ValueError(f"address must be 20 bytes, got {address!r}")
    return "0x" + ("0" * 24) + addr


def _topic_to_address(topic: str | bytes) -> str:
    if isinstance(topic, bytes):
        topic = "0x" + topic.hex()
    if not topic.startswith("0x") or len(topic) != 66:
        raise ValueError(f"unexpected topic format: {topic!r}")
    return "0x" + topic[-40:].lower()


def run(assignment_config: dict[str, Any], student_address: str) -> GraderResult:
    started = time.monotonic()

    try:
        proxy_raw = assignment_config["proxy_address"]
        from_block = int(assignment_config.get("from_block", 0))
        level_scores: dict[str, int] = {
            k.lower(): int(v) for k, v in assignment_config["level_scores"].items()
        }
        level_names: dict[str, str] = {
            k.lower(): v for k, v in assignment_config.get("level_names", {}).items()
        }
        thresholds = assignment_config.get("thresholds", {})
    except (KeyError, ValueError, TypeError) as exc:
        return GraderResult(
            status="error",
            score=None,
            details={"error": f"malformed config_json: {exc}"},
        )

    proxy = Web3.to_checksum_address(proxy_raw)
    max_score = int(thresholds.get("max_score", DEFAULT_MAX_SCORE))
    bonus_points = int(thresholds.get("bonus_points", DEFAULT_BONUS_POINTS))
    bonus_min_levels = int(thresholds.get("bonus_min_levels", DEFAULT_BONUS_MIN_LEVELS))

    try:
        player_topic = _player_topic(student_address)
    except ValueError as exc:
        return GraderResult(status="error", score=None, details={"error": str(exc)})

    w3 = get_web3()
    try:
        head = int(w3.eth.block_number)
    except (Web3Exception, Exception) as exc:  # noqa: BLE001
        return GraderResult(
            status="error",
            score=None,
            details={"error": f"rpc head fetch failed: {exc.__class__.__name__}: {exc}"},
        )

    topic0 = _topic0()
    solved_levels: dict[str, dict[str, Any]] = {}
    event_count = 0
    cursor = from_block

    while cursor <= head:
        chunk_to = min(cursor + CHUNK_BLOCKS - 1, head)
        try:
            logs = w3.eth.get_logs(
                {
                    "address": proxy,
                    "fromBlock": cursor,
                    "toBlock": chunk_to,
                    "topics": [topic0, player_topic, None, None],
                }
            )
        except (Web3Exception, Exception) as exc:  # noqa: BLE001
            return GraderResult(
                status="error",
                score=None,
                details={
                    "error": f"eth_getLogs failed at [{cursor}, {chunk_to}]: "
                    f"{exc.__class__.__name__}: {exc}",
                    "scanned_until_block": cursor - 1,
                    "events_seen": event_count,
                },
            )

        for log in logs:
            event_count += 1
            try:
                level_addr = _topic_to_address(log["topics"][3])
            except (KeyError, IndexError, ValueError):
                continue
            if level_addr in solved_levels:
                continue
            score = level_scores.get(level_addr)
            if score is None:
                continue
            solved_levels[level_addr] = {
                "level_address": level_addr,
                "level_name": level_names.get(level_addr, "?"),
                "score": score,
                "block_number": int(log.get("blockNumber", 0)),
            }

        cursor = chunk_to + 1

    raw_score = sum(int(v["score"]) for v in solved_levels.values())
    capped = min(max_score, raw_score)
    levels_solved = len(solved_levels)
    bonus = bonus_points if levels_solved >= bonus_min_levels else 0
    total = capped + bonus

    return GraderResult(
        status="ok",
        score=total,
        details={
            "player_address": student_address.lower(),
            "proxy_address": proxy,
            "scanned_block_range": [from_block, head],
            "event_count": event_count,
            "levels_solved": sorted(solved_levels.values(), key=lambda r: r["block_number"]),
            "raw_score": raw_score,
            "capped_score": capped,
            "bonus": bonus,
            "total": total,
            "thresholds": {
                "pass": int(thresholds.get("pass", 7)),
                "full_marks": int(thresholds.get("full_marks", 10)),
                "max_score": max_score,
                "bonus_points": bonus_points,
                "bonus_min_levels": bonus_min_levels,
            },
            "passed": raw_score >= int(thresholds.get("pass", 7)),
            "latency_ms": int((time.monotonic() - started) * 1000),
        },
    )
