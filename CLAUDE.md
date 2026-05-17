# CS423 Grading Platform — Project Memory

## Goal
Replace the public Google Sheet used to grade CS423 Blockchain
Technologies (New Uzbekistan University, Prof. Aleksandr Kapitonov) with
an automated, per-student-private grading platform. Phase 1 ships ONE
assignment end-to-end: Assignment 2 — Ethernaut.

## Phase 1 Acceptance
1. Student opens `http://localhost:5173`, clicks "Sign in with Ethereum",
   signs a nonce in MetaMask, lands on their own profile.
2. Profile lists Assignment 2 with a Submit button → backend runs the
   Ethernaut grader against Sepolia.
3. Grader reads `LevelCompletedLog` events from the OpenZeppelin Ethernaut
   proxy for the student's wallet, sums per-level scores from
   `assignments.config_json`, applies thresholds: `≥7 = pass`,
   `≥10 = full marks`, `≥15 levels solved = +4 bonus`.
4. Each run is APPENDED to `grader_runs` (never updated/deleted).
5. Student sees score, levels detected, and full history. No student can
   see another's data — every `/me/*` resolves from the session cookie.
6. `GET /api/health` returns `{ db: "ok", rpc_block_number: <int> }`.

## Tech Stack (do NOT substitute)
- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.x, Alembic, PostgreSQL 16,
  web3.py, siwe-py, psycopg v3 (not psycopg2), pydantic-settings.
- **Frontend**: React 18 + Vite + TypeScript, wagmi v2 + viem, TanStack
  Query, **plain CSS Modules** — no Tailwind, no React Router, no icon
  library. Keep deps minimal.
- **Auth**: SIWE / EIP-4361. Server-side single-use nonces, 5-min TTL.
  Verify marks nonce used and creates the session row in the SAME
  transaction. Session token = `secrets.token_urlsafe(32)`. Cookie
  httpOnly + SameSite=Lax, Secure controlled by `COOKIE_SECURE`. No JWT.

## Cross-platform (Windows + macOS) — hard constraints
- **NO Docker** anywhere. Postgres runs natively.
- **NO Makefile.** `tasks.py` at project root is the single entry point:
  `python tasks.py <cmd>` for `install|db-create|db-drop|migrate|seed-map|
  seed-dev|api|web|test|health`. Identical on Windows cmd, PowerShell,
  macOS Terminal.
- Python paths via `pathlib.Path`; no hardcoded `/` or `\`. No `bash`/`sh`
  or POSIX-only builtins. Subprocesses use `subprocess.run([...],
  shell=False)`.
- `db-create` uses the `psycopg` library as superuser (NOT `createdb`
  CLI). Prompts for password if `PG_SUPERUSER_PASSWORD` env var is unset.
- `tasks.py` auto-detects `.venv/` and uses its interpreter — no manual
  venv activation needed for tasks.
- `.gitattributes` forces LF for all text, CRLF for `*.ps1`.
- Frontend uses `cross-env` for any env vars in `package.json` scripts;
  no POSIX `&&` chains.

## Database (single 0001_init migration, schema only)
- `students(id, eth_address UNIQUE, name, student_id, github)`
- `assignments(id, code UNIQUE, title, weight, config_json JSONB)`
- `auth_nonces(id, address, nonce UNIQUE, created_at, used_at)`
- `sessions(id, token UNIQUE, address, created_at, expires_at)`
- `submissions(id, student_id FK, assignment_id FK, payload_json, created_at)`
- `grader_runs(id, submission_id FK, status, score, details_json, created_at)`
  — append-only.

All timestamps UTC. `eth_address` always lowercase.

## Env files
Each side owns its own; no project-root `.env`. `backend/.env` holds
`DATABASE_URL`, `SEPOLIA_RPC_URL`, SIWE/cookie settings. `frontend/.env`
holds `VITE_*` only.

## Scoring is data, not code
The grader **never hardcodes** the level→score map. `tasks.py seed-map`
fetches OZ gamedata, caps each level's `difficulty` at 5 (syllabus
complexity 0–5), writes map + proxy + thresholds + source URLs to
`assignments.config_json`. The grader reads `config_json` at run time;
the professor overrides scores via SQL on `config_json`, never by redeploy.

## Health endpoint
`GET /api/health` → `{ db: "ok", rpc_block_number: <int> }`. Backend
also fails loudly at boot if `SEPOLIA_RPC_URL` is missing — no silent
fallback to public RPCs.

## Ethernaut Reference (Sepolia)
- Proxy: `0xa3e7317E591D5A0F1c605be1b3aC4D2ae56104d6`
- Event: `LevelCompletedLog(address indexed player, address indexed
  instance, address indexed level)` — note the `Log` suffix.
- Sources (github.com/OpenZeppelin/ethernaut, master):
  `contracts/src/Ethernaut.sol`,
  `client/src/gamedata/deploy.sepolia.json`,
  `client/src/gamedata/gamedata.json`.

## Out of Scope (Phase 1)
LLM judge, on-chain attestations / Claude-token NFTs, weekly hash
anchor, graders for any other assignment, Telegram bot, production
deployment, ANY Dockerfile or docker-compose, professor-facing
student-registration UI (seed students via `tasks.py seed-dev`).

## Rules
- No secrets in code or migrations. `.env` gitignored, `.env.example` checked in.
- Frontend NEVER talks to Sepolia RPC. Backend only.
- Every grader run appends to `grader_runs`. Errors persisted with
  `status="error"` and a human-readable reason. Never silently fail.
- Commit after each working step with a clear message.
