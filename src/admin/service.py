# src/admin/service.py
from src.earn.service import get_task_stats
from src.wallet.service import get_all_wallets_summary
from src.safety.service import get_reports_stats, get_sos_stats

def get_dashboard_metrics() -> dict:
    tasks = get_task_stats()
    wallets = get_all_wallets_summary()
    reports = get_reports_stats()
    sos = get_sos_stats()
    return {
        "tasks": tasks,
        "wallets": wallets,
        "reports": reports,
        "sos": sos,
    }

def list_admin_reports(limit: int = 20) -> dict:
    return get_reports_stats(limit=limit)

def list_admin_sos(limit: int = 20) -> dict:
    return get_sos_stats(limit=limit)
