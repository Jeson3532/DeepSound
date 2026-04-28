import redis.asyncio as redis
from redis.asyncio import Redis
from redis.exceptions import RedisError
from fastapi import HTTPException
import os
import logging
from typing import Union

logger = logging.getLogger(__name__)
logging.basicConfig(level='DEBUG')

REDIS_URL = os.getenv("REDIS_URL")


class RedisManager:
    def __init__(self, url: str = REDIS_URL):
        self.url = url
        self._client: Union[Redis, None] = None

    @property
    def client(self) -> Redis:
        if not self._client:
            raise RuntimeError("Redis не инициализирован. Инициализируйте клиент через .initialize()")
        return self._client

    async def initialize(self, url: str = REDIS_URL, **kwargs) -> Redis:
        try:
            self._client = redis.from_url(url, socket_timeout=0.5, **kwargs)

            await self._client.ping()
            logger.info("Redis up.")
        except RedisError as e:
            logger.error(f"Ошибка при инициализации Redis: {e}")
            raise

    async def close(self):
        if self.client:
            await self.client.close()
            logger.info("Redis close.")
