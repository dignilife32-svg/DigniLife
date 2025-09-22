# src/utils/db_helpers.py
from __future__ import annotations
from sqlite3 import Connection
from typing import Any, Iterable, Mapping, Sequence, Tuple

# လုံးဝအလွယ်သုံးချင်လို့ types ကို လွတ်လပ်အောင် ထားရင် Pylance Errors မလာအောင် Any သုံး
def exec(db: Connection, sql: str, params: Iterable[Any] | Mapping[str, Any] = ()) -> None:
    # params တကယ် list/tuple မဟုတ်ရင် tuple ပြောင်း
    if not isinstance(params, (tuple, list, dict)):
        params = tuple([params])
    db.execute(sql, params if not isinstance(params, list) else tuple(params))
    db.commit()

def exec1(db: Connection, sql: str, params: Iterable[Any] | Mapping[str, Any] = ()) -> Tuple | None:
    if not isinstance(params, (tuple, list, dict)):
        params = tuple([params])
    cur = db.execute(sql, params if not isinstance(params, list) else tuple(params))
    return cur.fetchone()

def qi(n: int) -> str:
    """quick placeholders: qi(3) -> '?, ?, ?'"""
    return ", ".join(["?"] * n)
