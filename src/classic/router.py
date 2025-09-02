from fastapi import APIRouter

router = APIRouter()


@router.get("/tasks")
def list_classic_tasks():
    return {"tasks": ["simple-label", "micro-review"]}


@router.post("/submit")
def submit_classic(payload: dict):
    # classic earning flow handling ...
    return {"ok": True, "credited": 1.25}
