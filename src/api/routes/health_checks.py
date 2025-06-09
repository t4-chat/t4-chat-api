from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter(
    prefix="/health",
    tags=["health"]
)

@router.get("live")
def ping():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }