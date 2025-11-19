#!/usr/bin/env python3
# Weekly reconcile report generator (robust version)
import os, csv, sqlite3, datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RUNTIME_DIR = BASE_DIR / "runtime"
DB_PATH = RUNTIME_DIR / "night_worker_db.sqlite3"
REPORT_DIR = RUNTIME_DIR / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

def _qone(cur, sql, args=()):
    try:
        cur.execute(sql, args)
        row = cur.fetchone()
        return row
    except Exception:
        return None

def _qall(cur, sql, args=()):
    try:
        cur.execute(sql, args)
        return cur.fetchall()
    except Exception:
        return []

def generate_report():
    now = datetime.datetime.now(datetime.UTC).replace(microsecond=0)
    week_str = now.strftime("%Y-%m-%dT%H%MZ")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # withdrawals summary (handle status variety)
    withdrawals = _qall(
        c,
        """
        SELECT method, COUNT(*), IFNULL(SUM(amount_usd),0)
        FROM withdrawals
        WHERE status IN ('paid','ok','approved')
        GROUP BY method
        """
    )

    # earnings summary
    row = _qone(c, "SELECT COUNT(*), IFNULL(SUM(amount_usd),0) FROM earnings")
    earn_count, earn_sum = (int(row[0]), float(row[1])) if row else (0, 0.0)

    # current pool (kv)
    row = _qone(c, "SELECT value FROM kv WHERE key='pool_current_usd' LIMIT 1")
    pool_current = float(row[0]) if row and row[0] is not None else 0.0

    # conversions quick view
    row = _qone(c, "SELECT IFNULL(SUM(amount_usd),0), IFNULL(SUM(converted),0) FROM conversions")
    conv_usd_total, conv_target_total = (float(row[0]), float(row[1])) if row else (0.0, 0.0)

    conn.close()

    csv_path = REPORT_DIR / f"weekly_reconcile_{week_str}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["DigniLife Auto Reconcile Summary"])
        w.writerow(["Generated (UTC)", now.isoformat()])
        w.writerow([])
        w.writerow(["Withdrawals Summary"])
        w.writerow(["Method", "Count", "Total USD"])
        for m, cnt, tot in withdrawals:
            w.writerow([m or "", int(cnt or 0), round(float(tot or 0), 2)])
        if not withdrawals:
            w.writerow(["(none)", 0, 0.00])

        w.writerow([])
        w.writerow(["Earnings Summary", "Count", "Total USD"])
        w.writerow(["earnings", int(earn_count), round(float(earn_sum), 2)])

        w.writerow([])
        w.writerow(["Conversions Totals"])
        w.writerow(["Total USD (source)", round(conv_usd_total, 2)])
        w.writerow(["Total Converted (target sum)", round(conv_target_total, 2)])

        w.writerow([])
        w.writerow(["Current Pool USD", round(pool_current, 2)])

    print(f"[reconcile] Weekly report created → {csv_path}")
    return csv_path

if __name__ == "__main__":
    generate_report()
