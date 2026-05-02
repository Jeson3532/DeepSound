from fastapi import APIRouter, Body, Request, HTTPException, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.auth import authorize
from src.schemas.base.auth import UserLogin, UserRegister
from src.schemas.response.auth import UserRegisterResponse
from src.services.database.redis.service import RedisService
from src.services.database.pg.engine import get_session
from src.services.database.pg.service import DatabaseService
from src.services.audio.extract import get_mel_spec
from src.services.audio.service import AudioService
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
router = APIRouter(prefix="/audio", tags=["Audio Analyze"])


@router.post("/analyze")
async def analyze_audio(request: Request, audio: UploadFile = File(...)):
    session_id = request.headers.get("X-Session-Id")
    if not session_id:
        raise HTTPException(status_code=401, detail="No session")

    redis_client = request.app.state.redis
    username = await RedisService(redis_client).get_session(session_id)
    if not username:
        raise HTTPException(status_code=401, detail="Session expired")
    audio_bytes = await audio.read()
    audio_service: AudioService = request.app.state.audio_service
    response = await audio_service.analyze(audio_bytes)
    logger.info(f"RESPONSE: {response}")
    return response
