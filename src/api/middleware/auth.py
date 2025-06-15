from typing import Callable
from uuid import UUID

from fastapi import Request
from fastapi.responses import JSONResponse

from src.services.auth.token_service import TokenService

from src.config import settings


def create_auth_middleware(token_service_instance: TokenService) -> Callable:
    async def auth_middleware(request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        # Skip authentication for public endpoints
        if request.url.path in [
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health/live",
            "/health/logs",
            "/api/auth/google",
            "/api/ai-providers",
            "/api/ai-models",
        ] or request.url.path.startswith("/static/"):
            return await call_next(request)

        # Check for valid authentication header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Unauthorized: Missing or invalid authentication token"
                },
            )

        # Validate token
        token = auth_header.replace("Bearer ", "")
        payload = token_service_instance.validate_token(token)

        if not payload:
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized: Invalid or expired token"},
            )

        if request.url.path.startswith("/api/admin"):
            if payload.get("email") not in settings.ADMIN_EMAILS:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Unauthorized: User is not an admin"},
                )

        # Set user ID in request state and continue
        request.state.user_id = UUID(payload.get("sub"))
        request.state.user_email = payload.get("email")
        return await call_next(request)

    return auth_middleware
