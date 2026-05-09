# CS423 Grading Platform — Phase 1 MVP

Automated grading platform for CS423 Blockchain Technologies (New Uzbekistan
University, Prof. Aleksandr Kapitonov). Phase 1 ships **one** assignment
end-to-end: Assignment 2 — Ethernaut, graded by reading `LevelCompletedLog`
events from the OpenZeppelin Ethernaut proxy on Sepolia.

See `CLAUDE.md` for scope, stack, and out-of-scope items.

## Prerequisites

- Python 3.11
- Node 20+ and npm
- Postgres 16 running locally (e.g. Postgres.app, or `brew services start postgresql@16`)
- An Alchemy Sepolia RPC key
- MetaMask in your browser

## Quickstart

```bash
cp .env.example .env
# Edit .env: paste your Alchemy key into SEPOLIA_RPC_URL

make install        # backend venv + frontend npm
make db-create      # creates role 'cs423' and database 'cs423_grading'
make migrate        # alembic upgrade head
make seed-map       # fetches OZ Ethernaut gamedata, populates assignment config
make seed-dev       # inserts sample student rows

# In one terminal:
make api            # FastAPI on http://localhost:8000

# In another:
make web            # Vite on http://localhost:5173
```

Then open <http://localhost:5173>, click **Sign in with Ethereum**, sign the
message with MetaMask. You'll land on your profile page with Assignment 2
listed and a Submit button.

## Smoke test

```bash
make health
# {"db":"ok","rpc_block_number":12345678}
```

If `rpc_block_number` is missing or the API errors, your `SEPOLIA_RPC_URL`
is wrong. The backend refuses to start without it — there is no fallback
to public RPCs.

## How grading works

The Ethernaut grader (`backend/app/graders/ethernaut.py`) does **not**
hardcode the level→score map. At seed time, `seed_ethernaut_map.py` pulls
the official `gamedata.json` and `deploy.sepolia.json` from
[OpenZeppelin/ethernaut](https://github.com/OpenZeppelin/ethernaut), caps
each level's `difficulty` at 5 (syllabus complexity is 0–5), and writes the
result into `assignments.config_json`. The professor overrides individual
level scores by editing `config_json` directly in Postgres.

Every grader run appends a row to `grader_runs` — runs are never updated
or deleted. Students see their own history; cross-student access is
structurally impossible (every `/me/*` endpoint resolves the student from
the session cookie).

## Project layout

```
backend/    FastAPI app, alembic migrations, graders/, scripts/
frontend/   Vite + React + wagmi v2
docs/       architecture notes, per-assignment grader specs
Makefile    db-create / migrate / seed-map / seed-dev / api / web / test
```
