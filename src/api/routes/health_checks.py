from datetime import datetime, timezone

from fastapi import APIRouter

from src.logging.logging_config import get_logger

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
def ping():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/logs")
def logs():
    logger = get_logger(__name__)
    logger.debug("DEBUG message")
    logger.info("INFO message")
    logger.warning("WARNING message")
    logger.error("ERROR message")
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}
