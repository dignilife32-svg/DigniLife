#!/usr/bin/env python3
import time, subprocess, datetime, os, sys

RETENTION_DAYS = int(os.environ.get("EVID_RETENTION_DAYS", "180"))  # default 6 months
KEEP_LATEST = int(os.environ.get("EVID_KEEP_LATEST", "30"))         # always keep last 30 zips
INTERVAL_SEC = 7 * 24 * 3600                                        # run every 7 days

def run_once():
    print(f"[auto_cleanup] {datetime.datetime.utcnow().isoformat()}Z running cleaner…")
    cmd = [
        sys.executable, os.path.join("runtime","legal_evidence","cleanup.py"),
        "--retention-days", str(RETENTION_DAYS),
        "--keep-latest", str(KEEP_LATEST),
    ]
    subprocess.run(cmd, check=False)

if __name__ == "__main__":
    while True:
        run_once()
        time.sleep(INTERVAL_SEC)
