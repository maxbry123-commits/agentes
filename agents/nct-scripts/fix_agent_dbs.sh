#!/bin/bash
# /opt/nct/scripts/fix_agent_dbs.sh
# Recreate SQLite schema in agent memory.db (idempotent)
set -e
for agent in claude mimo openclaw; do
  db=/opt/nct/agents/$agent/memory.db
  echo "=== FIXING $agent DB ($db) ==="
  python3 <<PYEOF
import sqlite3
c = sqlite3.connect('$db', timeout=10)
c.execute('PRAGMA journal_mode=WAL')
c.execute('PRAGMA wal_checkpoint(TRUNCATE)')
c.executescript("""
CREATE TABLE IF NOT EXISTS state(key TEXT PRIMARY KEY, value TEXT, updated_at TEXT);
CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, content TEXT, meta TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY AUTOINCREMENT, status TEXT, prompt TEXT, result TEXT, attempts INTEGER DEFAULT 0, created_at TEXT, finished_at TEXT, error TEXT);
CREATE TABLE IF NOT EXISTS heartbeat(id INTEGER PRIMARY KEY AUTOINCREMENT, pid INTEGER, ram_mb REAL, cpu TEXT, last_task TEXT, status TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT, target TEXT, payload TEXT, created_at TEXT);
""")
c.commit()
tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
print(f"  $agent tables: {tables}")
print(f"  $agent state rows: {c.execute('SELECT count(*) FROM state').fetchone()[0]}")
c.close()
PYEOF
done
echo "=== FIX COMPLETE ==="
