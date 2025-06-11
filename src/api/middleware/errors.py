import traceback
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from src.services.errors.errors import NotFoundError, ForbiddenError
from src.logging.logging_config import get_logger

logger = get_logger(__name__)

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except NotFoundError as e:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": str(e)}
            )
        except ForbiddenError as e:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": str(e)}
            )
        except Exception as e:
            logger.error(f"Internal server error: {str(e)}")
            logger.error(traceback.format_exc())
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )
