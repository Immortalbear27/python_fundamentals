import hashlib
from abc import ABC, abstractmethod

class BaseCache(ABC):
    @abstractmethod
    def get(self, key: str):
        raise NotImplementedError

    @abstractmethod
    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        raise NotImplementedError


class NoopCache(BaseCache):
    def get(self, key: str):
        return None

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        return

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        return True


class RedisCache(BaseCache):
    def __init__(self, host="localhost", port=6379, db=0):
        import redis
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        self.client.ping()

    def get(self, key: str):
        return self.client.get(key)

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        self.client.setex(key, ttl_seconds, value)

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        current = self.client.incr(key)
        if current == 1:
            self.client.expire(key, window_seconds)
        return current <= limit


def line_cache_key(line: str) -> str:
    digest = hashlib.sha256(line.encode("utf-8")).hexdigest()
    return f"loglevel:{digest}"
