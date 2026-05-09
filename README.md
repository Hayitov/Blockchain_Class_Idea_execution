# CS423 Grading Platform — Phase 1 MVP

Automated grading platform for **CS423 Blockchain Technologies** (New
Uzbekistan University, Prof. Aleksandr Kapitonov). Phase 1 ships **one**
assignment end-to-end: Assignment 2 — Ethernaut, graded by reading
`LevelCompletedLog` events from the OpenZeppelin Ethernaut proxy on Sepolia.

See `CLAUDE.md` for scope, stack, and out-of-scope items.
See `docs/grader_assignment_2_ethernaut.md` for the grader algorithm.

## What's working

1. Student opens <http://localhost:5173>, clicks **Sign in with Ethereum**,
   signs a nonce in MetaMask, lands on their own profile.
2. Profile lists Assignment 2 with a **Submit** button. Click → backend
   runs the Ethernaut grader against Sepolia.
3. Result is appended to `grader_runs` (never overwritten). The student
   sees their score, levels detected, and full submission history.
4. No student can see another student's data — every `/me/*` endpoint
   resolves the student from the session cookie only.

## Prerequisites

- Python 3.11
- Node 20+ and npm
- Postgres 16 running locally (e.g. Postgres.app, or
  `brew services start postgresql@16`)
- An Alchemy Sepolia RPC key — sign up free at <https://www.alchemy.com>
- MetaMask in your browser (any Chromium- or Firefox-based)

## Quickstart

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
# Edit backend/.env: paste your Alchemy key into SEPOLIA_RPC_URL.
# The backend refuses to boot without it — there is no public-RPC fallback.

make install        # backend venv + frontend npm
make db-create      # creates role 'cs423' and database 'cs423_grading'
make migrate        # alembic upgrade head — schema only
make seed-map       # fetches OZ Ethernaut gamedata into assignments.config_json
make seed-dev       # inserts two sample student rows (replace before prod)

# Terminal 1:
make api            # FastAPI on http://localhost:8000

# Terminal 2:
make web            # Vite on http://localhost:5173
```

Open <http://localhost:5173>, connect MetaMask, sign in.

## Smoke tests

**Stack-up check** (DB + Sepolia RPC reachable):

```bash
make health
# {"db":"ok","rpc_block_number":12345678}
```

If `rpc_block_number` is missing, your `SEPOLIA_RPC_URL` is wrong. Fix it,
then restart `make api`.

**Grader against a real wallet** (no UI, no auth):

```bash
cd backend && . .venv/bin/activate
python -m scripts.run_grader_cli 0xYourAddressThatHasSolvedEthernautLevels
```

Prints the full grader details (levels detected, scanned block range,
score) — useful for separating "is the grader correct" from "is the SIWE
flow correct".

**Backend unit tests** (mocked web3, no network):

```bash
make test
# 9 passed
```

## Manual end-to-end test

1. Run all of Quickstart above with a valid Alchemy key.
2. `make health` returns 200 with a current block number.
3. Edit `backend/scripts/seed_dev_data.py` so `student_active.eth_address`
   is the wallet you'll sign in with. Re-run `make seed-dev`.
4. Sign in via the browser, click **Submit** on Assignment 2.
5. Confirm the score, levels list, and history appear.
6. Sign out, sign in with a *different* MetaMask account that's also
   seeded as a student. Confirm you see only that student's data.

## How grading works

The grader **never hardcodes** the level→score map. At seed time,
`backend/scripts/seed_ethernaut_map.py` pulls `gamedata.json` and
`deploy.sepolia.json` from
[OpenZeppelin/ethernaut](https://github.com/OpenZeppelin/ethernaut), caps
each level's `difficulty` at 5 (syllabus complexity is 0–5), and writes the
result into `assignments.config_json` along with the proxy address, the
syllabus thresholds, and source URLs.

To override a level's score, the professor edits the JSONB column directly:

```sql
UPDATE assignments
SET config_json = jsonb_set(
  config_json,
  '{level_scores,0x7e0f53981657345b31c59ac44e9c21631ce710c7}',
  '3'::jsonb
)
WHERE code = 'assignment_2_ethernaut';
```

No redeploy. The next grader run picks up the new score.

Every grader run appends a row to `grader_runs`. Rows are never updated or
deleted. Errors (RPC down, bad config) are persisted with `status="error"`
and a human-readable reason — graders never silently fail.

## Project layout

```
backend/    FastAPI + SQLAlchemy 2 + Alembic + web3 + siwe
  app/      app, auth/, routes/, graders/
  alembic/  single 0001_init migration
  scripts/  seed_ethernaut_map, seed_dev_data, run_grader_cli
  tests/    grader unit tests
frontend/   Vite + React 18 + wagmi v2 + TanStack Query (CSS modules)
docs/       grader spec
Makefile    db-create / migrate / seed-map / seed-dev / api / web / test
```

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Backend refuses to start: `Field required: SEPOLIA_RPC_URL` | `.env` not created or the var is empty. |
| `make health` shows `rpc_block_number: null` and an `rpc_error` | Bad Alchemy key or Alchemy rate limit. |
| `make db-create` errors `role "$USER" does not exist` | Pass `make db-create PG_SUPERUSER=postgres` (or whatever your superuser is). |
| Sign-in fails with `domain mismatch` | `SIWE_DOMAIN` in `.env` doesn't match the host you opened the browser at. Default is `localhost:5173`. |
| `make seed-map` fails fetching gamedata | Network or GitHub is down. Re-run later; the script is idempotent. |
| Grader returns score 0 with no events | The wallet hasn't solved any Ethernaut levels on Sepolia, OR `from_block` is too high. Default is 4,000,000 — well before deployment. |

## Out of scope (Phase 1)

LLM judge, on-chain attestations / "Claude tokens", weekly hash anchor,
graders for any other assignment, Telegram bot, production deployment, app
Dockerfiles, professor-facing student-registration UI. See `CLAUDE.md`.
