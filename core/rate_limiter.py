import time
from collections import defaultdict
from threading import Lock
from typing import Tuple, Optional
from core.config_manager import config


class RateLimiter:
    """
    In-memory rate limiter using a sliding window algorithm.
    Tracks requests per IP and per API Key.
    """

    def __init__(self):
        self.lock = Lock()
        # {key: [timestamps]}
        self.history = defaultdict(list)
        self.calls = 0

    def _prune_expired_unlocked(self, now: float, window_seconds: int) -> None:
        """Pruge expired identities dynamically to prevent memory leaks under long running load."""
        inactive_identities = []
        for ident, ts_list in list(self.history.items()):
            valid_ts = [ts for ts in ts_list if now - ts < window_seconds]
            if not valid_ts:
                inactive_identities.append(ident)
            else:
                self.history[ident] = valid_ts
        for ident in inactive_identities:
            if ident in self.history:
                del self.history[ident]

    def is_allowed(self, identity: str, limit: int, window_seconds: int = 60) -> bool:
        """
        Returns True if the identity is allowed to make a request.
        identity: IP address or API Key.
        limit: Max requests in the window.
        window_seconds: The time window in seconds.
        """
        if limit <= 0:
            return True  # Unlimited

        now = time.time()
        with self.lock:
            self.calls += 1
            if self.calls % 100 == 0:
                self._prune_expired_unlocked(now, window_seconds)

            # Clean old timestamps
            valid_ts = [
                ts for ts in self.history[identity] if now - ts < window_seconds
            ]

            if len(valid_ts) < limit:
                valid_ts.append(now)
                self.history[identity] = valid_ts
                return True

            # If not allowed, clean up key if valid_ts is completely empty to prevent memory leak
            if not valid_ts:
                if identity in self.history:
                    del self.history[identity]
            else:
                self.history[identity] = valid_ts
            return False

    def get_remaining(self, identity: str, limit: int, window_seconds: int = 60) -> int:
        now = time.time()
        with self.lock:
            self.calls += 1
            if self.calls % 100 == 0:
                self._prune_expired_unlocked(now, window_seconds)

            valid_ts = [
                ts for ts in self.history[identity] if now - ts < window_seconds
            ]
            if not valid_ts:
                if identity in self.history:
                    del self.history[identity]
            else:
                self.history[identity] = valid_ts
            return max(0, limit - len(valid_ts))


# Singleton instances for different scopes
ip_limiter = RateLimiter()
api_limiter = RateLimiter()


def check_access(ip: str, api_key: Optional[str] = None) -> Tuple[bool, str]:
    """
    High-level check for both IP and API Key limits.
    Returns (allowed, reason).
    """
    # 1. Global IP Limit
    ip_limit = config.get("rate_limit.requests_per_minute", 100)  # req per minute
    if not ip_limiter.is_allowed(ip, ip_limit, 60):
        return False, "Rate limit exceeded for IP."

    # 2. API Key Limit (if provided and different from default)
    if api_key and api_key != "gravity-local":
        key_limit = config.get("security.rate_limit_api", 1000)
        if not api_limiter.is_allowed(api_key, key_limit, 60):
            return False, "Rate limit exceeded for API Key."

    return True, ""
