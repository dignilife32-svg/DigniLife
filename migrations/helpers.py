from alembic import op

def has_index(table: str, name: str) -> bool:
    rows = op.get_bind().exec_driver_sql(f"PRAGMA index_list('{table}')").fetchall()
    return any(r[1] == name for r in rows)

def drop_index_if_exists(name: str, table: str):
    if has_index(table, name):
        op.drop_index(name, table_name=table)
