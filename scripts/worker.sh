#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH=src

# Optional envs (override in .env or shell)
export WORKER_RUNTIME_DIR="${WORKER_RUNTIME_DIR:-runtime}"
export WORKER_DB_FILE="${WORKER_DB_FILE:-night_worker_db.sqlite3}"
export NIGHT_LOOP_INTERVAL_SECS="${NIGHT_LOOP_INTERVAL_SECS:-12}"
export ALLOW_TASKS="${ALLOW_TASKS:-hash_small,small_embedding,image_denoise}"

uvicorn worker:app --host 127.0.0.1 --port 18000 --reload

curl -s http://127.0.0.1:18000/status | jq      # check earn + balance 

python - <<'PY'    # earn total check
import sqlite3, json
c=sqlite3.connect("runtime/night_worker_db.sqlite3").cursor()
out={
  "pool_usd": float((c.execute("select value from kv where key='pool_current_usd'").fetchone() or [0])[0]),
  "paid_total_usd": float((c.execute("select coalesce(sum(amount_usd),0) from withdrawals where status like 'paid%'").fetchone() or [0])[0]),
  "earned_total_usd": float((c.execute("select coalesce(sum(amount_usd),0) from earnings").fetchone() or [0])[0]),
}
print(json.dumps(out, indent=2))
PY

# 1) start
python worker.py &
sleep 1

# 2) health + pool
curl -s http://127.0.0.1:18000/health
curl -s http://127.0.0.1:18000/balance | jq

# 3) start loop
curl -s -X POST http://127.0.0.1:18000/start -H 'content-type: application/json' -d '{"interval_sec":2}' | jq

# 4) status (should show running + lasts grow)
curl -s http://127.0.0.1:18000/status | jq '.ok,.running,.interval_sec,.lasts|length'

# 5) withdraw → auto_approve and pool decreased
curl -s -X POST http://127.0.0.1:18000/withdraw -H 'content-type: application/json' \
  -d '{"user_id":"admin","amount_usd":50,"method":"ewallet","dest":"mywave","face_scan_verified":true}' | jq

# AI task auto + checker scripts
python - <<'PY'
import sqlite3, json
c = sqlite3.connect("runtime/night_worker_db.sqlite3").cursor()
rows = c.execute("SELECT ts_utc, device, task, amount_usd FROM earnings ORDER BY ts_utc DESC LIMIT 20").fetchall()
out = [dict(ts_utc=r[0], device=r[1], task=r[2], amount_usd=r[3]) for r in rows]
print(json.dumps(out, indent=2))
PY

# evidence 243445455.zip run
python legal_evidence.py

# sqlite3 DB check scripts for python -c
python -c "import sqlite3, json; con=sqlite3.connect('runtime/night_worker_db.sqlite3'); cur=con.cursor(); print(json.dumps(cur.execute('select wid, amount_usd, target, converted, ts_utc from conversions order by ts_utc desc limit 3;').fetchall(), indent=2)); con.close()"

# realtime withdraw scripts
curl -s -X POST http://127.0.0.1:18000/admin/mark_paid_fx \
  -H "Content-Type: application/json" \
  --data-raw '{
    "amount_usd": 100,
    "target_currency": "MYR",
    "method": "tng_prepaid",
    "dest": "+601175492783",
    "note": "real-time withdraw test $100"
  }'

uvicorn gateway_server:app --host 127.0.0.1 --port 19000 --reload
# payout gateway local only 

POST /payout/request
{
   "id": "wd_0001",
   "amount_usd": 300,
   "country": "MY",
   "bank": "TNG",
   "dest": "0179622131"
}

# withdraw/payout tng
→ Phone unlock
→ Open TNG
→ DuitNow Mobile
→ Enter Number
→ Enter Amount
→ Confirm
→ TNG balance တိုး
→ DONE

$env:PAYOUT_GATEWAY_ENABLED = "1"   # server gateway run
uvicorn worker:app --host 127.0.0.1 --port 18000 --reload
