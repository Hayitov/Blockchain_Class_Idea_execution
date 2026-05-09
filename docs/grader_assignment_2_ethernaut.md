# Grader spec — Assignment 2 (Ethernaut)

## Inputs

| Source | Value |
|---|---|
| Student | `student.eth_address` (taken from the session, never from the request) |
| Config | `assignments.config_json` for the row with `code='assignment_2_ethernaut'` |

The grader trusts the cookie-resolved student address as the ground-truth
player. The `config_json` is the only source for the proxy address, the
`from_block` lower bound, the level→score map, and the syllabus thresholds.

## Algorithm

1. Compute `topic0 = keccak256("LevelCompletedLog(address,address,address)")`.
2. Build `topic1` = the player address left-padded to 32 bytes.
3. Loop from `config.from_block` to the current Sepolia head in
   `CHUNK_BLOCKS` (50,000) windows. Each iteration calls `eth_getLogs` with:
   - `address = config.proxy_address`
   - `topics = [topic0, topic1, null, null]`
4. For each returned log, extract `topic[3]` → level contract address
   (lowercased). If `config.level_scores` does not contain that address,
   skip it (defense in depth — should never happen).
5. Deduplicate by level address. A student can complete the same level
   twice; we count it once.
6. Compute:
   - `raw_score = sum(level_scores[addr] for addr in distinct_levels)`
   - `capped = min(config.thresholds.max_score, raw_score)`
   - `bonus = config.thresholds.bonus_points if len(distinct_levels) >= config.thresholds.bonus_min_levels else 0`
   - `total = capped + bonus`
   - `passed = raw_score >= config.thresholds.pass`

## Output

A single append-only row in `grader_runs`:

| column | value |
|---|---|
| `status` | `"ok"` or `"error"` |
| `score` | `total` on ok, `null` on error |
| `details_json` | full audit trail — see below |

`details_json` schema on success:

```jsonc
{
  "player_address": "0x…",
  "proxy_address": "0xa3e7…04d6",
  "scanned_block_range": [4000000, 6543210],
  "event_count": 7,                // total LevelCompletedLog events seen
  "levels_solved": [
    { "level_address": "0x…", "level_name": "Hello Ethernaut",
      "score": 0, "block_number": 4123456 },
    …
  ],
  "raw_score": 12,
  "capped_score": 10,
  "bonus": 4,
  "total": 14,
  "passed": true,
  "thresholds": { "pass": 7, "full_marks": 10, "max_score": 10,
                  "bonus_points": 4, "bonus_min_levels": 15 },
  "latency_ms": 2840
}
```

`details_json` on error:

```jsonc
{
  "error": "<human-readable reason>",
  // when partial scan occurred:
  "scanned_until_block": 5012345,
  "events_seen": 3
}
```

## Failure modes

| Cause | What we do |
|---|---|
| Missing/bad `SEPOLIA_RPC_URL` | Backend refuses to boot. `/api/health` would 503 first. |
| Sepolia RPC down mid-scan | One `grader_runs` row with `status="error"` and the partial scan range. |
| Malformed `config_json` | One `grader_runs` row with `status="error"`; never silent. |
| Player address malformed | Same as above. |
| Unknown level address in a log | Log skipped (level isn't in our scoring map). Counted in `event_count`. |

## Where the scoring data comes from

`backend/scripts/seed_ethernaut_map.py` fetches two files from
`github.com/OpenZeppelin/ethernaut@master`:

- `client/src/gamedata/gamedata.json` — `levels[].difficulty` (0–7) and `name`.
- `client/src/gamedata/deploy.sepolia.json` — per-level Sepolia addresses.

Each level's score is `min(int(difficulty), 5)` (syllabus complexity is 0–5).
Source URLs and `fetched_at` are recorded in `config_json.source`. The
professor overrides any individual level's score by editing
`config_json.level_scores` in Postgres directly — no redeploy needed.

## CLI smoke test

Bypass the UI and the SIWE flow when verifying RPC + scoring against a
known-active wallet:

```bash
make seed-map                                        # populate config_json
python -m scripts.run_grader_cli 0xYourSepoliaAddr   # from inside backend/ venv
```

Output is the full `details_json` plus status/score, as if it had been
written to `grader_runs`.
