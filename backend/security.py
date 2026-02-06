import bleach
import time
from collections import defaultdict, deque
from typing import Dict, Tuple

# --- Sanitization ---

def sanitize_text(text: str) -> str:
    """
    Cleans text to prevent XSS.
    Allowed tags: None (Plain text only).
    """
    if not text:
        return ""
    # bleach.clean default allows some tags, we want NONE.
    return bleach.clean(text, tags=[], attributes={}, strip=True)

# --- Rate Limiting ---

class RateLimiter:
    """
    Token Bucket implementation for rate limiting.
    """
    def __init__(self, rate: float, capacity: int):
        self.rate = rate          # Tokens per second
        self.capacity = capacity  # Max tokens (burst size)
        self.tokens = capacity
        self.last_update = time.time()

    def allow(self) -> bool:
        now = time.time()
        elapsed = now - self.last_update
        
        # Refill tokens
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_update = now
        
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

class RateLimitManager:
    def __init__(self):
        # Map: client_id -> RateLimiter
        # We use a tuple (room_id, user_id) as client_id for finer granularity
        self.limiters: Dict[str, RateLimiter] = {}
        
        # Configuration
        self.USER_RATE = 5.0      # 5 requests/sec per user
        self.USER_BURST = 10      # Allow burst of 10
        
        # Cleanup tracker
        self.last_cleanup = time.time()

    def check_limit(self, client_id: str) -> bool:
        """
        Returns True if request is allowed, False if rate limited.
        """
        self._cleanup_if_needed()
        
        if client_id not in self.limiters:
            self.limiters[client_id] = RateLimiter(self.USER_RATE, self.USER_BURST)
            
        return self.limiters[client_id].allow()

    def _cleanup_if_needed(self):
        """
        Prevent memory leak by cleaning up stale limiters every 5 minutes.
        """
        now = time.time()
        if now - self.last_cleanup > 300:
            # Simple cleanup: clear all. 
            # Active users will recreate their limiters on next request.
            # This is acceptable for a rate limiter.
            self.limiters.clear()
            self.last_cleanup = now

# Singleton
rate_limiter = RateLimitManager()
