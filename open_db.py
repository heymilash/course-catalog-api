"""Open psql using the same .env settings as the API; no credentials in arguments."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess

from sqlalchemy.engine import make_url

from config import settings


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pg-bin", default=r"C:\Program Files\PostgreSQL\17\bin")
    args = parser.parse_args()
    executable = shutil.which("psql") or str(Path(args.pg_bin) / "psql.exe")
    url = make_url(settings.database_url)
    env = dict(os.environ, PGCLIENTENCODING="UTF8")
    if url.password is not None:
        env["PGPASSWORD"] = url.password
    command = [executable, "-X", "-h", url.host or "localhost", "-p", str(url.port or 5432),
               "-U", url.username or "catalog_app", "-d", url.database or "course_catalog"]
    print(f"Database {url.database}, port {url.port or 5432}. Try \\dt or \\d courses; quit with \\q.")
    raise SystemExit(subprocess.call(command, env=env))
