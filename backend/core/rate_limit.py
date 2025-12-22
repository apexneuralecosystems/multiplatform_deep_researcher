"""
Rate limiting configuration using SlowAPI.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse


# Create limiter instance
limiter = Limiter(key_func=get_remote_address)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": str(exc.detail),
            "retry_after": exc.detail.split("per")[1].strip() if "per" in str(exc.detail) else "60 seconds"
        }
    )


# Rate limit decorators for common use cases
# Usage: @limiter.limit("10/minute")
# 
# Common limits:
# - "10/minute" - 10 requests per minute
# - "100/hour" - 100 requests per hour  
# - "5/second" - 5 requests per second
# - "1000/day" - 1000 requests per day
