import time
from collections import defaultdict
import asyncio

class RateLimiter:
    def __init__(self, max_calls: int = 10, period: float = 60.0):
        self.max_calls = max_calls
        self.period = period
        self.users = defaultdict(list)
        self.lock = asyncio.Lock()

    async def is_allowed(self, user_id: int) -> bool:
        async with self.lock:
            now = time.monotonic()
            calls = self.users[user_id]
            # Remove old timestamps
            while calls and calls[0] < now - self.period:
                calls.pop(0)
            if len(calls) >= self.max_calls:
                return False
            calls.append(now)
            return True

# Global rate limiters (can be instantiated in main)
action_limiter = RateLimiter(max_calls=10, period=60)  # general actions
game_start_limiter = RateLimiter(max_calls=5, period=30)  # starting games