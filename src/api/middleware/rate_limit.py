import time
from collections import defaultdict

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


# Simple in-memory rate limiting
class SimpleRateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)

    def is_allowed(self, ip: str, limit: int = 100, window: int = 60):
        """Check if request is allowed (limit requests per window seconds)"""
        now = time.time()
        # Clean old requests
        self.requests[ip] = [req_time for req_time in self.requests[ip] if now - req_time < window]

        # Check if under limit
        if len(self.requests[ip]) >= limit:
            return False

        # Add current request
        self.requests[ip].append(now)
        return True


# Create rate limiter instance
rate_limiter = SimpleRateLimiter()


# Global rate limiting middleware
async def rate_limit_middleware(request: Request, call_next):
    # Skip rate limiting for health checks and public endpoints
    if request.url.path in ["/health/live", "/health/logs", "/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)

    # Get client IP
    client_ip = request.client.host if request.client else "unknown"

    # Check rate limit (100 requests per minute)
    if not rate_limiter.is_allowed(client_ip, limit=100, window=60):
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Rate limit exceeded. Maximum 100 requests per minute allowed.",
                "retry_after": 60
            },
            headers={"Retry-After": "60"}
        )

    response = await call_next(request)
    return response
