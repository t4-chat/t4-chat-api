from datetime import datetime, timezone

from fastapi import APIRouter

from src.logging.logging_config import get_logger

router = APIRouter(prefix="/health", tags=["Health Checks"])


@router.get("/live")
def ping():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}
