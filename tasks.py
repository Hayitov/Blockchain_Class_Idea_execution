"""Cross-platform task runner for the CS423 grading platform.

Single entry point for both Windows and macOS. Run from project root:

    python tasks.py <command>

Commands: install | db-create | db-drop | migrate | seed-map | seed-dev
          api | web | test | health
"""

from __future__ import annotations

import getpass
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
VENV = BACKEND / ".venv"

DB_NAME = os.environ.get("DB_NAME", "cs423_grading")
DB_USER = os.environ.get("DB_USER", "cs423")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "cs423")
PG_HOST = os.environ.get("PG_HOST", "localhost")
PG_PORT = int(os.environ.get("PG_PORT", "5432"))


# ---------- helpers ----------

def venv_python() -> Path:
    if os.name == "nt":
        return VENV / "Scripts" / "python.exe"
    return VENV / "bin" / "python"


def require_venv() -> Path:
    py = venv_python()
    if not py.exists():
        sys.exit(
            f"Backend venv not found at {VENV}. Run `python tasks.py install` first."
        )
    return py


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> int:
    printable = " ".join(str(c) for c in cmd)
    print(f"$ {printable}" + (f"  (cwd={cwd})" if cwd else ""))
    result = subprocess.run(cmd, cwd=str(cwd) if cwd else None, shell=False)
    if check and result.returncode != 0:
        sys.exit(result.returncode)
    return result.returncode


def resolve(executable: str) -> str:
    path = shutil.which(executable)
    if not path:
        sys.exit(f"Required tool not found on PATH: {executable}")
    return path


# ---------- commands ----------

def cmd_install() -> None:
    if not VENV.exists():
        print(f"Creating venv at {VENV} using {sys.executable}")
        run([sys.executable, "-m", "venv", str(VENV)])
    else:
        print(f"Reusing existing venv at {VENV}")
    py = venv_python()
    run([str(py), "-m", "pip", "install", "--upgrade", "pip"])
    run([str(py), "-m", "pip", "install", "-e", ".[dev]"], cwd=BACKEND)
    run([resolve("npm"), "install"], cwd=FRONTEND)
    print("\nInstall complete.")


def _pg_connect(superuser: str, password: str | None):
    import psycopg  # type: ignore

    kwargs = {
        "host": PG_HOST,
        "port": PG_PORT,
        "user": superuser,
        "dbname": "postgres",
        "autocommit": True,
    }
    if password is not None:
        kwargs["password"] = password
    return psycopg.connect(**kwargs)


def _pg_superuser_connection():
    try:
        import psycopg  # noqa: F401
    except ImportError:
        sys.exit(
            "psycopg not installed. Run `python tasks.py install` first, "
            "then re-run this command with `python tasks.py db-create`."
        )

    superuser = os.environ.get("PG_SUPERUSER") or getpass.getuser()
    env_password = os.environ.get("PG_SUPERUSER_PASSWORD")

    if env_password is not None:
        return _pg_connect(superuser, env_password)

    # Try peer / trust auth first (common on macOS Homebrew, dev Linux).
    import psycopg  # type: ignore

    try:
        return _pg_connect(superuser, None)
    except psycopg.OperationalError:
        pass

    # Fall back to interactive prompt.
    pw = getpass.getpass(f"Postgres password for superuser '{superuser}': ")
    return _pg_connect(superuser, pw)


def cmd_db_create() -> None:
    from psycopg import sql  # type: ignore

    with _pg_superuser_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (DB_USER,))
        if cur.fetchone() is None:
            cur.execute(
                sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(
                    sql.Identifier(DB_USER), sql.Literal(DB_PASSWORD)
                )
            )
            print(f"Created role {DB_USER!r}.")
        else:
            print(f"Role {DB_USER!r} already exists.")

        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
        if cur.fetchone() is None:
            cur.execute(
                sql.SQL("CREATE DATABASE {} OWNER {}").format(
                    sql.Identifier(DB_NAME), sql.Identifier(DB_USER)
                )
            )
            print(f"Created database {DB_NAME!r} owned by {DB_USER!r}.")
        else:
            print(f"Database {DB_NAME!r} already exists.")

    print(f"DB ready: {DB_NAME} owned by {DB_USER}")


def cmd_db_drop() -> None:
    """Drop the cs423_grading database. DESTRUCTIVE — dev only."""
    from psycopg import sql  # type: ignore

    with _pg_superuser_connection() as conn, conn.cursor() as cur:
        cur.execute(
            sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(DB_NAME))
        )
    print(f"Dropped database {DB_NAME!r}.")


def cmd_migrate() -> None:
    py = require_venv()
    run([str(py), "-m", "alembic", "upgrade", "head"], cwd=BACKEND)


def cmd_seed_map() -> None:
    py = require_venv()
    run([str(py), "-m", "scripts.seed_ethernaut_map"], cwd=BACKEND)


def cmd_seed_dev() -> None:
    py = require_venv()
    run([str(py), "-m", "scripts.seed_dev_data"], cwd=BACKEND)


def cmd_api() -> None:
    py = require_venv()
    run(
        [
            str(py),
            "-m",
            "uvicorn",
            "app.main:app",
            "--reload",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ],
        cwd=BACKEND,
    )


def cmd_web() -> None:
    run([resolve("npm"), "run", "dev"], cwd=FRONTEND)


def cmd_test() -> None:
    py = require_venv()
    run([str(py), "-m", "pytest", "-q"], cwd=BACKEND)


def cmd_health() -> None:
    import json
    import urllib.error
    import urllib.request

    url = "http://localhost:8000/api/health"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.URLError as exc:
        sys.exit(f"Cannot reach {url}: {exc.reason}. Is `python tasks.py api` running?")

    try:
        print(json.dumps(json.loads(body), indent=2))
    except json.JSONDecodeError:
        print(body)


# ---------- dispatch ----------

COMMANDS: dict[str, Callable[[], None]] = {
    "install": cmd_install,
    "db-create": cmd_db_create,
    "db-drop": cmd_db_drop,
    "migrate": cmd_migrate,
    "seed-map": cmd_seed_map,
    "seed-dev": cmd_seed_dev,
    "api": cmd_api,
    "web": cmd_web,
    "test": cmd_test,
    "health": cmd_health,
}


def print_help() -> None:
    print(__doc__)
    print("Available commands:")
    for name in COMMANDS:
        print(f"  {name}")


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] in {"-h", "--help", "help"}:
        print_help()
        return
    name = argv[1]
    fn = COMMANDS.get(name)
    if fn is None:
        print(f"Unknown command: {name}\n")
        print_help()
        sys.exit(2)
    fn()


if __name__ == "__main__":
    main(sys.argv)
