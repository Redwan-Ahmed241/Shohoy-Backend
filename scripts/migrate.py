"""
Applies the SQL files in migrations/ (in name order) to the database in SUPABASE_DB_URL.

    python scripts/migrate.py          # shows the target database and asks for confirmation
    python scripts/migrate.py --yes    # no prompt (CI / scripted deploys)

Every migration is idempotent, so re-running one is safe. The local SQLite database does
not need this: it creates its tables automatically.
"""
import pathlib
import sys
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402


def main() -> int:
    if not config.SUPABASE_DB_URL:
        print("SUPABASE_DB_URL is not set - the local SQLite database creates its own tables. Nothing to do.")
        return 0

    target = urlparse(config.SUPABASE_DB_URL)
    files = sorted((ROOT / "migrations").glob("*.sql"))
    print(f"Target database: {target.hostname}:{target.port or 5432}{target.path}")
    for f in files:
        print(f"  - {f.name}")
    if "--yes" not in sys.argv and input("Apply these migrations? Type 'yes': ").strip().lower() != "yes":
        print("Cancelled.")
        return 1

    engine = create_engine(config.SUPABASE_DB_URL)
    # AUTOCOMMIT so each file's own BEGIN ... COMMIT controls its transaction
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        for f in files:
            conn.exec_driver_sql(f.read_text(encoding="utf-8"))
            print(f"applied {f.name}")
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
