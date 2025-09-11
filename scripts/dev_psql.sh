
#!/usr/bin/env bash
set -euo pipefail

# 1) activate venv (Git Bash / WSL)
source venv/Scripts/activate  # Windows Git Bash OK (WSL হলে venv/bin/activate)

# 2) envs
export PYTHONPATH=".:$PYTHONPATH"
export DB_URL='postgresql+psycopg://appuser:apppass@localhost:5432/dignilife'

# 3) ensure deps (quiet + skip pip version check)
python -m pip install -q --disable-pip-version-check "psycopg[binary]" "python-multipart"

# 4) migrate + seed
alembic upgrade head
python -m src.admin.seed

# 5) run app
python -m uvicorn src.main:app --reload
