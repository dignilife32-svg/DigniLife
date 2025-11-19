# check_db.py
import sqlite3, sys

db = sys.argv[1] if len(sys.argv) > 1 else "data/dev.db"  # <- default
con = sqlite3.connect(db)
cur = con.cursor()

print("DB:", db)

print("\n=== TABLES ===")
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
for (name,) in cur.fetchall():
    print("-", name)

def show(name):
    print(f"\n=== {name.upper()} ===")
    cur.execute(f"PRAGMA table_info({name});")
    rows = cur.fetchall()
    if rows:
        for r in rows:
            print(r)
    else:
        print("(table not found)")

for t in ("daily_tasks", "wallet_ledger"):
    show(t)

con.close()
