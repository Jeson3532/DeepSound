from fastapi import APIRouter, Body, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.auth import authorize
from src.schemas.base.auth import UserLogin, UserRegister
from src.schemas.response.auth import UserRegisterResponse
from src.services.database.redis.service import RedisService
from src.services.database.pg.engine import get_session
from src.services.database.pg.service import DatabaseService

router = APIRouter(prefix="/audio", tags=["Audio Analyze"])

