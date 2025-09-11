# require version 7
$ErrorActionPreference = "Stop"

# 1) activate venv (PowerShell)
$venvActivate = Join-Path -Path "venv" -ChildPath "Scripts\Activate.ps1"
. $venvActivate

# 2) env / path
$env:PYTHONPATH = "."

# 3) SQLite fallback
$env:DB_URL = ""
$env:DB_SQLITE = "sqlite:///./dignilife.db"

# 4) ensure deps
pip install --quiet "psycopg[binary]" python-multipart

# 5) migrate + seed
alembic upgrade head
python -m src.admin.seed

# 6) run app
uvicorn src.main:app --reload
