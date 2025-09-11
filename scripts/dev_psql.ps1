# scripts/dev_psql.ps1
$ErrorActionPreference = "Stop"

# 1) activate venv
. .\venv\Scripts\Activate.ps1

# 2) envs
$env:PYTHONPATH = ".;$env:PYTHONPATH"
$env:DB_URL = "postgresql+psycopg://appuser:apppass@localhost:5432/dignilife"

# 3) ensure deps
python -m pip install --quiet --disable-pip-version-check "psycopg[binary]" "python-multipart"

# 4) migrate + seed
alembic upgrade head
python -m src.admin.seed

# 5) run app
python -m uvicorn src.main:app --reload
