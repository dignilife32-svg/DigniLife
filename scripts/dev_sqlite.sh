#!/usr/bin/env bash
set -e

# 1) activate venv (Git Bash / WSL)
source venv/Scripts/activate 2>/dev/null || source venv/bin/activate

# 2) env / path
export PYTHONPATH=.

# 3) SQLite fallback URL (local file)
export DB_URL=
export DB_SQLITE="sqlite:///./dignilife.db"

# 4) ensure deps (quiet)
pip install -q "psycopg[binary]" python-multipart

# 5) migrate + seed
alembic upgrade head
python -m src.admin.seed

# 6) run app
uvicorn src.main:app --reload
