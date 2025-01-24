from fastapi import HTTPException, Request
from typing import Dict, Tuple
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, requests_per_minute: int = 30):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)

    def is_rate_limited(self, key: str) -> Tuple[bool, float]:
        now = time.time()
        minute_ago = now - 60

        self.requests[key] = [req_time for req_time in self.requests[key] if req_time > minute_ago]

        if len(self.requests[key]) >= self.requests_per_minute:
            wait_time = 60 - (now - self.requests[key][0])
            return True, wait_time

        self.requests[key].append(now)
        return False, 0

rate_limiter = RateLimiter()

async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    is_limited, wait_time = rate_limiter.is_rate_limited(client_ip)

    if is_limited:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Too Many Requests",
                "wait_seconds": round(wait_time, 1)
            }
        )

    response = await call_next(request)
    return response 