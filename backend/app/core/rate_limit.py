import time
from typing import Dict, List, Tuple
from fastapi import Request, HTTPException, status
from app.core.config import settings

# Key -> List of timestamps
_request_windows: Dict[str, List[float]] = {}


async def check_rate_limit(request: Request, limit: int = settings.RATE_LIMIT_PER_HOUR, window_seconds: int = 3600) -> Tuple[int, int, int]:
    """
    Sliding window rate limiter per client IP or authenticated user.
    Returns (limit, remaining, reset_time_seconds)
    """
    now = time.time()
    # Determine identifier (User ID if authenticated or Client IP)
    client_ip = request.client.host if request.client else "unknown"
    auth_header = request.headers.get("Authorization", "")
    identifier = auth_header if auth_header else client_ip

    if identifier not in _request_windows:
        _request_windows[identifier] = []

    # Clean old requests outside window
    cutoff = now - window_seconds
    _request_windows[identifier] = [t for t in _request_windows[identifier] if t > cutoff]

    current_requests = len(_request_windows[identifier])
    remaining = max(0, limit - current_requests)
    reset_seconds = int(window_seconds - (now - (_request_windows[identifier][0] if _request_windows[identifier] else now)))

    if current_requests >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {limit} requests per hour allowed. Try again in {reset_seconds} seconds.",
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_seconds),
            },
        )

    _request_windows[identifier].append(now)
    return limit, remaining - 1, reset_seconds
