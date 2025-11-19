import sqlite3

conn = sqlite3.connect("dignilife.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT,
    email TEXT
)
""")

cur.execute("INSERT OR IGNORE INTO users (id, name, email) VALUES (?, ?, ?)", (
    "demo_user", "Demo", "demo@dignilife.ai"
))

conn.commit()
conn.close()

print("✅ demo_user created.")
