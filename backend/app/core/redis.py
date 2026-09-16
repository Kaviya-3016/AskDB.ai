import json
import time
from typing import Any, Optional
import redis.asyncio as redis
from app.core.config import settings

# In-memory fallback cache dictionary when Redis server is unreachable or disabled
_memory_cache = {}
_memory_cache_expiry = {}


class CacheService:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        if settings.REDIS_ENABLED:
            try:
                self.redis_client = redis.from_url(
                    settings.REDIS_URL, decode_responses=True
                )
            except Exception:
                self.redis_client = None

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve value from Redis or in-memory fallback."""
        if self.redis_client:
            try:
                val = await self.redis_client.get(key)
                if val is not None:
                    return json.loads(val)
            except Exception:
                pass

        # Check in-memory fallback
        if key in _memory_cache:
            exp = _memory_cache_expiry.get(key)
            if exp and time.time() > exp:
                del _memory_cache[key]
                del _memory_cache_expiry[key]
                return None
            return _memory_cache[key]
        return None

    async def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """Store value with TTL in Redis or in-memory fallback."""
        serialized = json.dumps(value)
        if self.redis_client:
            try:
                await self.redis_client.set(key, serialized, ex=ttl_seconds)
                return True
            except Exception:
                pass

        # Set in-memory fallback
        _memory_cache[key] = value
        if ttl_seconds > 0:
            _memory_cache_expiry[key] = time.time() + ttl_seconds
        return True

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if self.redis_client:
            try:
                await self.redis_client.delete(key)
            except Exception:
                pass
        if key in _memory_cache:
            del _memory_cache[key]
        if key in _memory_cache_expiry:
            del _memory_cache_expiry[key]
        return True

    async def clear_prefix(self, prefix: str) -> int:
        """Clear all keys starting with prefix."""
        count = 0
        keys_to_del = [k for k in _memory_cache.keys() if k.startswith(prefix)]
        for k in keys_to_del:
            await self.delete(k)
            count += 1
        return count


cache_service = CacheService()
