# src/daily/router.py
from fastapi import APIRouter

# Keep an empty router to avoid broken imports from old code
router = APIRouter(prefix="/daily", tags=["daily"])

# (No endpoints here for now; /task/submit lives in src/earn/router.py)
