import time, datetime, subprocess

INTERVAL_SEC = 7 * 24 * 3600  # run every 7 days

def run_once():
    print(f"[auto_reconcile] {datetime.datetime.utcnow().isoformat()}Z generating weekly report...")
    subprocess.run(["python", "scheduler/auto_reconcile.py"], check=False)

if __name__ == "__main__":
    while True:
        run_once()
        time.sleep(INTERVAL_SEC)
