import redis.asyncio as redis
from redis.asyncio import Redis
from redis.exceptions import RedisError
from fastapi import HTTPException
import os
import logging
from typing import Union
from src.services.database.redis.engine import RedisManager

logger = logging.getLogger(__name__)
logging.basicConfig(level='DEBUG')

SESSION_EXPIRE = 7200


class RedisService:
    def __init__(self, client: Redis):
        self._client = client

    async def create_session(self, session_id: int, username: str, exp: int = SESSION_EXPIRE) -> bool:
        try:
            response = await self._client.set(f"session:{session_id}", username, ex=exp)
            if response:
                return True
            return False
        except RedisError as e:
            logger.error(f"Ошибка при создании сессии Redis: {e}")
            return False
