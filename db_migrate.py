#!/usr/bin/env python3
"""
Standalone DB migration script for production.

Usage:
    python db_migrate.py              # migrate users.db in current dir
    python db_migrate.py --db /path/to/users.db
    python db_migrate.py --check      # dry-run: show pending migrations only

The script:
  1. Creates a timestamped backup before any changes
  2. Applies only the migrations that are missing (idempotent)
  3. Prints a summary of what was applied

This is a safety wrapper around the same migrations that init_db() runs
automatically at server startup. Use it on production when you want to
apply the schema changes without restarting the Flask process.
"""

import os
import sys
import shutil
import sqlite3
import argparse
from datetime import datetime

DB_DEFAULT = os.path.join(os.path.dirname(__file__), 'users.db')

# ---------------------------------------------------------------------------
# Migration definitions — each entry is (description, callable(cursor))
# ---------------------------------------------------------------------------

def _m_history_notes_model_used(c):
    c.execute("PRAGMA table_info(history)")
    if 'notes_model_used' not in {r[1] for r in c.fetchall()}:
        c.execute("ALTER TABLE history ADD COLUMN notes_model_used TEXT DEFAULT ''")
        return True
    return False

def _m_history_openai_usage(c):
    c.execute("PRAGMA table_info(history)")
    if 'openai_usage_history' not in {r[1] for r in c.fetchall()}:
        c.execute("ALTER TABLE history ADD COLUMN openai_usage_history TEXT DEFAULT ''")
        return True
    return False

def _m_history_project_id(c):
    c.execute("PRAGMA table_info(history)")
    if 'project_id' not in {r[1] for r in c.fetchall()}:
        c.execute("ALTER TABLE history ADD COLUMN project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL")
        return True
    return False

def _m_history_image_path(c):
    c.execute("PRAGMA table_info(history)")
    if 'image_path' not in {r[1] for r in c.fetchall()}:
        c.execute("ALTER TABLE history ADD COLUMN image_path TEXT")
        return True
    return False

def _m_users_role(c):
    c.execute("PRAGMA table_info(users)")
    if 'role' not in {r[1] for r in c.fetchall()}:
        c.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
        # Bootstrap admin from env or hardcoded fallback
        admin_email = os.environ.get('ADMIN_EMAIL', 'wmarzec@gmail.com').strip()
        c.execute("UPDATE users SET role = 'admin' WHERE email = ?", (admin_email,))
        return True
    return False

def _m_chat_history_model_used(c):
    c.execute("PRAGMA table_info(chat_history)")
    cols = {r[1] for r in c.fetchall()}
    changed = False
    if 'model_used' not in cols:
        c.execute("ALTER TABLE chat_history ADD COLUMN model_used TEXT DEFAULT ''")
        changed = True
    if 'openai_usage_history' not in cols:
        c.execute("ALTER TABLE chat_history ADD COLUMN openai_usage_history TEXT DEFAULT ''")
        changed = True
    return changed

MIGRATIONS = [
    ("history: add notes_model_used",       _m_history_notes_model_used),
    ("history: add openai_usage_history",   _m_history_openai_usage),
    ("history: add project_id",             _m_history_project_id),
    ("history: add image_path",             _m_history_image_path),
    ("users:   add role + set admin",       _m_users_role),
    ("chat_history: add model_used + usage",_m_chat_history_model_used),
]

# ---------------------------------------------------------------------------

def backup(db_path: str) -> str:
    ts   = datetime.now().strftime('%Y%m%d_%H%M%S')
    dest = f"{db_path}.backup_{ts}"
    shutil.copy2(db_path, dest)
    return dest


def run(db_path: str, dry_run: bool = False) -> None:
    if not os.path.exists(db_path):
        print(f"ERROR: database not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    size_mb = os.path.getsize(db_path) / 1024 / 1024
    print(f"Database : {db_path}  ({size_mb:.2f} MB)")

    if dry_run:
        print("Mode     : dry-run (no changes)\n")
    else:
        bk = backup(db_path)
        print(f"Backup   : {bk}\n")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    c = conn.cursor()

    applied = 0
    skipped = 0

    for desc, fn in MIGRATIONS:
        if dry_run:
            # Run in a savepoint, check result, then roll back
            c.execute("SAVEPOINT dry_check")
            try:
                changed = fn(c)
            except Exception as e:
                c.execute("ROLLBACK TO dry_check")
                print(f"  ERROR  {desc}: {e}")
                continue
            c.execute("ROLLBACK TO dry_check")
            status = "PENDING" if changed else "ok    "
        else:
            try:
                changed = fn(c)
            except Exception as e:
                print(f"  ERROR  {desc}: {e}")
                conn.rollback()
                continue
            status = "APPLIED" if changed else "ok    "
            if changed:
                applied += 1
            else:
                skipped += 1

        print(f"  {status}  {desc}")

    if not dry_run:
        conn.commit()
        print(f"\nDone. Applied: {applied}, already up-to-date: {skipped}")
    else:
        pending = sum(
            1 for _, fn in MIGRATIONS
            if _probe(conn, fn)
        )
        print(f"\nPending migrations: {pending}")

    conn.close()


def _probe(conn, fn) -> bool:
    c = conn.cursor()
    c.execute("SAVEPOINT probe")
    try:
        result = fn(c)
    except Exception:
        result = False
    c.execute("ROLLBACK TO probe")
    return bool(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ProjectSTT — DB migration tool')
    parser.add_argument('--db',    default=DB_DEFAULT, help='Path to users.db')
    parser.add_argument('--check', action='store_true',  help='Dry-run: show pending migrations only')
    args = parser.parse_args()
    run(args.db, dry_run=args.check)
