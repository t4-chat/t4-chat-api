from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(
    prefix="/health",
    tags=["health"]
)

@router.get("/live")
def ping():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }