from __future__ import annotations

import hashlib
import logging
import time
import uuid

from app.core.config import settings

try:
    from redis import Redis
except ImportError:  # pragma: no cover - production installs redis from requirements.txt
    Redis = None


logger = logging.getLogger("workbench.contact_rate_limit")

RATE_LIMIT_SCRIPT = """
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local cutoff = now - window * 1000
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', cutoff)
local count = redis.call('ZCARD', KEYS[1])
if count >= limit then
  local first = redis.call('ZRANGE', KEYS[1], 0, 0, 'WITHSCORES')
  local retry = 1
  if first[2] then
    retry = math.max(1, math.ceil((tonumber(first[2]) + window * 1000 - now) / 1000))
  end
  return {0, retry}
end
redis.call('ZADD', KEYS[1], now, ARGV[4])
redis.call('EXPIRE', KEYS[1], window + 1)
return {1, 0}
"""


class ContactRateLimiter:
    ATTEMPT_LIMIT = 5
    ATTEMPT_WINDOW_SECONDS = 10 * 60
    SUCCESS_COOLDOWN_SECONDS = 60
    IDEMPOTENCY_TTL_SECONDS = 10 * 60

    def __init__(self):
        self._client = None
        if settings.redis_url and Redis is not None:
            self._client = Redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1,
            )

    @staticmethod
    def _subject_key(ip: str) -> str:
        return hashlib.sha256(ip.encode("utf-8")).hexdigest()

    def check_attempt(self, ip: str) -> tuple[bool | None, int]:
        """Return (allowed, retry_after). None means Redis is unavailable."""
        if self._client is None:
            return None, 0
        key = f"contact:attempt:{self._subject_key(ip)}"
        try:
            result = self._client.eval(
                RATE_LIMIT_SCRIPT,
                1,
                key,
                int(time.time() * 1000),
                self.ATTEMPT_WINDOW_SECONDS,
                self.ATTEMPT_LIMIT,
                uuid.uuid4().hex,
            )
            return bool(int(result[0])), int(result[1])
        except Exception:
            logger.warning("Redis attempt rate limit unavailable", exc_info=True)
            return None, 0

    def is_in_success_cooldown(self, ip: str) -> tuple[bool | None, int]:
        if self._client is None:
            return None, 0
        key = f"contact:success:{self._subject_key(ip)}"
        try:
            ttl = self._client.ttl(key)
            return ttl > 0, max(1, ttl) if ttl > 0 else 0
        except Exception:
            logger.warning("Redis success cooldown unavailable", exc_info=True)
            return None, 0

    def mark_success(self, ip: str) -> None:
        if self._client is None:
            return
        try:
            self._client.setex(
                f"contact:success:{self._subject_key(ip)}",
                self.SUCCESS_COOLDOWN_SECONDS,
                "1",
            )
        except Exception:
            logger.warning("Redis success cooldown write failed", exc_info=True)

    def reserve_idempotency(self, key: str, request_hash: str) -> str:
        """Return reserved, same, different, or unavailable."""
        if self._client is None:
            return "unavailable"
        redis_key = f"contact:idempotency:{key}"
        try:
            current = self._client.get(redis_key)
            if current is None:
                if self._client.set(redis_key, request_hash, nx=True, ex=self.IDEMPOTENCY_TTL_SECONDS):
                    return "reserved"
                current = self._client.get(redis_key)
            return "same" if current == request_hash else "different"
        except Exception:
            logger.warning("Redis idempotency unavailable", exc_info=True)
            return "unavailable"


contact_rate_limiter = ContactRateLimiter()
