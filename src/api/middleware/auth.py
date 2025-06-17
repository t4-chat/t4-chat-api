from typing import Callable, Optional, Tuple
from uuid import UUID

from fastapi import Request
from fastapi.responses import JSONResponse

from src.services.auth.token_service import TokenService

from src.config import settings


def create_auth_middleware(token_service_instance: TokenService) -> Callable:
    def extract_and_validate_token(auth_header: Optional[str]) -> Optional[dict]:
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.replace("Bearer ", "")
        return token_service_instance.validate_token(token)

    def set_user_context(request: Request, payload: dict) -> None:
        request.state.user_id = UUID(payload.get("sub"))
        request.state.user_email = payload.get("email")

    async def auth_middleware(request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        # Skip authentication for public endpoints
        if (
            request.url.path
            in [
                "/",
                "/docs",
                "/redoc",
                "/openapi.json",
                "/health/live",
                "/health/logs",
                "/api/auth/google",
                "/api/ai-providers",
            ]
            or request.url.path.startswith("/static/")
            or request.url.path.startswith("/api/chats/shared/")
        ):
            return await call_next(request)

        # Handle optional authentication for /api/ai-models
        if request.url.path == "/api/ai-models":
            auth_header = request.headers.get("Authorization")
            payload = extract_and_validate_token(auth_header)
            if payload:
                set_user_context(request, payload)
            return await call_next(request)

        # Handle required authentication for all other protected endpoints
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized: Missing or invalid authentication token"},
            )

        payload = extract_and_validate_token(auth_header)
        if not payload:
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized: Invalid or expired token"},
            )

        # Check admin access for admin endpoints
        if request.url.path.startswith("/api/admin"):
            if payload.get("email") not in settings.ADMIN_EMAILS:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Unauthorized: User is not an admin"},
                )

        set_user_context(request, payload)
        return await call_next(request)

    return auth_middleware
