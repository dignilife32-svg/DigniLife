import time, subprocess, datetime

INTERVAL_DAYS = 3  # every 3 days

while True:
    print(f"[auto_archive] {datetime.datetime.utcnow()} running evidence pack…")
    subprocess.run(["python", "runtime/legal_evidence/auto_pack.py"])
    time.sleep(INTERVAL_DAYS * 24 * 3600)
