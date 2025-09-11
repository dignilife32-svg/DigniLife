import os
from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool
from src.db.session import Base  # your models metadata

config = context.config
fileConfig(config.config_file_name)

# --- DB URL with fallback ---
db_url = (
    os.getenv("DB_URL") or
    os.getenv("DB_SQLITE") or
    "sqlite:///./dignilife.db"
)
config.set_main_option("sqlalchemy.url", db_url)

target_metadata = Base.metadata
