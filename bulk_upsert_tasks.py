# bulk_upsert_tasks.py
import os, sys
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, Column, String, Boolean, Text, DateTime, Float, select, insert, update
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
try:
    from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
except Exception:
    PG_JSONB = None

def json_type_for(engine):
    if engine.url.get_backend_name().startswith("postgres") and PG_JSONB is not None:
        return PG_JSONB
    return SQLITE_JSON

def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python bulk_upsert_tasks.py <csv_path>")

    csv_path = sys.argv[1]
    db_url = os.environ.get("DATABASE_URL","sqlite:///./tasks_seed.db")
    table = os.environ.get("TABLE_NAME","daily_tasks")
    schema = os.environ.get("SCHEMA")

    engine = create_engine(db_url, future=True)
    meta = MetaData(schema=schema)
    JSONType = json_type_for(engine)

    tasks = Table(table, meta,
        Column("code", String(64), primary_key=True),
        Column("name", String(255), nullable=False),
        Column("category", String(32), nullable=False),
        Column("display_value_usd", Float, nullable=False),
        Column("expected_time_sec", Float, nullable=False),
        Column("ai_required", Boolean, nullable=False, default=True),
        Column("prereq_gate", Boolean, nullable=False, default=False),
        Column("languages", String(255), nullable=False, default="auto"),
        Column("description", Text),
        Column("user_prompt", Text),
        Column("quality_rubric", Text),
        Column("bonus_eligible", String(255)),
        Column("review_threshold", Float, nullable=False, default=0.7),
        Column("is_active", Boolean, nullable=False, default=True),
        Column("notes", Text),
        Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
        extend_existing=True,
    )
    meta.create_all(engine, tables=[tasks])

    df = pd.read_csv(csv_path)
    required = {"code","name","category","display_value_usd","expected_time_sec","ai_required","prereq_gate","languages","is_active","review_threshold"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"Missing required columns: {missing}")

    df["created_at"] = pd.Timestamp.utcnow()
    records = df.to_dict(orient="records")

    with engine.begin() as conn:
        existing = {row[0] for row in conn.execute(select(tasks.c.code))}
        for r in records:
            if r["code"] in existing:
                conn.execute(update(tasks).where(tasks.c.code==r["code"]).values(**r))
            else:
                conn.execute(insert(tasks).values(**r))
    print(f"Upserted {len(records)} tasks into {(schema+'.' if schema else '')+table}")

if __name__ == "__main__":
    main()
