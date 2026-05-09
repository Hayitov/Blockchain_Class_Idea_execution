# CS423 Grading Platform — Project Memory

## Goal
Replace the public Google Sheet currently used to grade the CS423 Blockchain
Technologies course at New Uzbekistan University (Prof. Aleksandr Kapitonov)
with an automated, per-student-private grading platform. Phase 1 ships ONE
assignment end-to-end as a working demo: Assignment 2 — Ethernaut.

## Phase 1 Acceptance Criteria
1. Student opens `localhost:5173`, clicks "Sign in with Ethereum", signs a
   nonce in MetaMask, lands on their own profile page.
2. Profile lists Assignment 2 with a "Submit" button. Click → backend runs
   the Ethernaut grader.
3. Grader queries the OZ Ethernaut proxy on Sepolia for `LevelCompletedLog`
   events emitted by the student's wallet. It sums per-level complexity
   scores from a static map and applies syllabus thresholds:
   `≥7 = pass`, `≥10 = full marks`, `≥15 distinct levels solved = +4 bonus`.
4. Each grader run is appended to `grader_runs` (never updated).
5. Student sees their score, levels detected, and run history. No student
   can see another student's data.
6. README with one-command setup: `docker compose up` + a make target.

## Tech Stack (do NOT substitute)
- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.x, Alembic, PostgreSQL 16,
  web3.py (Sepolia RPC).
- **Frontend**: React 18 + Vite + TypeScript, **Tailwind CSS** (v3),
  **React Router v6**, **lucide-react** for icons. wagmi v2 + viem for
  SIWE, TanStack Query for server state.
- **Local infra**: no Docker. Postgres 16 runs on the host (e.g. Postgres.app
  or `brew services start postgresql@16`). FastAPI and Vite also on the host.
  Quickstart: `make db-create` → `make migrate` → `make seed-map` →
  `make seed-dev` → `make api` (in one terminal) + `make web` (in another).
- **Auth**: SIWE / EIP-4361. Server-side single-use nonces, 5-minute TTL.
  On verify, issue an httpOnly session cookie. No JWT, no passwords.

## Database (minimum)
- `students(id, eth_address, name, student_id, github)`
- `assignments(id, code, title, weight, config_json)`
- `auth_nonces(address, nonce, created_at, used_at)`
- `sessions(token, address, created_at, expires_at)`
- `submissions(id, student_id, assignment_id, payload_json, created_at)`
- `grader_runs(id, submission_id, status, score, details_json, created_at)`
  — append-only, never updated.

## Project Layout
```
/backend          FastAPI app, alembic migrations, graders/, scripts/
  .env            (gitignored)
  .env.example    (checked in)
/frontend         Vite + React app, Tailwind, React Router
  .env            (gitignored)
  .env.example    (checked in)
/docs             architecture notes, per-assignment grader specs
Makefile          db-create / migrate / seed-map / seed-dev / api / web / test
CLAUDE.md         this file
README.md         run instructions
```

## Env files
Each side owns its own env file. There is **no project-root `.env`**.
- `backend/.env` — `DATABASE_URL`, `SEPOLIA_RPC_URL`, SIWE/cookie/session settings.
- `frontend/.env` — Vite-prefixed vars (`VITE_*`) only. The browser only ever sees `VITE_*`, never the backend's.

## Out of Scope (Phase 1)
- LLM / Claude judge integration
- On-chain attestations or "Claude token" NFTs
- Weekly on-chain hash anchor of the gradebook
- Graders for any assignment other than Assignment 2 (Ethernaut)
- Telegram bot
- Production deployment, app Dockerfiles
- Professor-facing student-registration UI (students seeded via SQL fixture)

## Rules
- No private keys / API tokens / secrets in code or migrations. Use `.env`
  (gitignored) with `.env.example` checked in.
- All times in UTC.
- Frontend never talks to Sepolia RPC directly. Only the backend does, so
  the RPC URL stays secret and we can cache / rate-limit.
- `SEPOLIA_RPC_URL` is required. Backend fails loudly at boot if missing —
  no silent fallback to a public RPC.
- Commit after each working step with a clear message.

## Scoring is data, not code
The Ethernaut grader **never hardcodes** the level→score map. At seed time,
`backend/scripts/seed_ethernaut_map.py` fetches the OpenZeppelin gamedata
files (URLs below), caps each level's `difficulty` at 5 (syllabus complexity
range is 0–5), and writes the result to `assignments.config_json` for the
`assignment_2_ethernaut` row. The grader reads `config_json` at run time.
The professor overrides individual level scores by editing `config_json`
in the DB — never by redeploying. The seed script also records the source
URLs and the cap rule in `config_json.source` and at the top of its file.

## Health endpoint
`GET /api/health` → `{ db: "ok", rpc_block_number: <int> }`. This is the
smoke test for "is the whole stack wired up" and exists before any grader
logic. It calls the backend's web3 client to fetch the latest Sepolia
block, so a missing/bad `SEPOLIA_RPC_URL` is caught immediately.

## Ethernaut Reference (Sepolia) — verified sources
- Proxy (events emitted here): `0xa3e7317E591D5A0F1c605be1b3aC4D2ae56104d6`
- Implementation (do NOT query directly): `0x49662cAeF8386f84d99873c34280E24d3e742e4f`
- Per-level addresses: `client/src/gamedata/deploy.sepolia.json` keys `"0"`–`"40"` (41 levels).
- Event (note the `Log` suffix; the kickoff prompt called it `LevelCompleted`,
  but the on-chain name is `LevelCompletedLog`):
  ```solidity
  event LevelCompletedLog(
    address indexed player,
    address indexed instance,
    address indexed level
  );
  ```
- Sources (github.com/OpenZeppelin/ethernaut, master):
  - `contracts/src/Ethernaut.sol`
  - `client/src/gamedata/deploy.sepolia.json`
  - `client/src/gamedata/gamedata.json`

## Long-Term Vision (not Phase 1)
Per-student dashboards; SIWE login for all; auto-graders per assignment
(Sepolia, Polkadot, TON, web pages); Claude as judge for subjective work;
soulbound "Claude token" NFTs minted per student carrying a hash of the
verdict + the AI judge's prompt; weekly on-chain anchor of the full
gradebook.
