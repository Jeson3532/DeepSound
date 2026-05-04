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
async def analyze_audio(request: Request, audio: UploadFile = File(...), session: AsyncSession = Depends(get_session)):
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

    db = DatabaseService(session)
    await db.history.save_analysis(username, {
        "file_name": audio.filename,
        "label": response["label"],
        "confidence": response["confidence"],
        "is_defect": response["defect"],
        "sample_rate": response.get("metrics", {}).get("file_info", {}).get("sample_rate"),
        "duration_sec": response.get("metrics", {}).get("file_info", {}).get("duration_sec"),
        "rms_level": response.get("metrics", {}).get("deep_analysis", {}).get("rms_level"),
        "peak_level": response.get("metrics", {}).get("deep_analysis", {}).get("peak_level"),
        "spectral_bandwidth": response.get("metrics", {}).get("deep_analysis", {}).get("spectral_bandwidth"),
        "spectral_rolloff": response.get("metrics", {}).get("deep_analysis", {}).get("spectral_rolloff"),
        "zcr": response.get("metrics", {}).get("deep_analysis", {}).get("zcr"),
    })
    logger.info(f"RESPONSE: {response}")
    return response


@router.get("/history")
async def get_history(request: Request, session: AsyncSession = Depends(get_session)):
    session_id = request.headers.get("X-Session-Id")
    if not session_id:
        raise HTTPException(status_code=401, detail="No session")
    redis_client = request.app.state.redis
    username = await RedisService(redis_client).get_session(session_id)
    if not username:
        raise HTTPException(status_code=401, detail="Session expired")

    db = DatabaseService(session)
    records = await db.history.get_user_history(username)
    return [
        {
            "id": r.id,
            "file_name": r.file_name,
            "label": r.label,
            "confidence": r.confidence,
            "is_defect": r.is_defect,
            "sample_rate": r.sample_rate,
            "duration_sec": r.duration_sec,
            "rms_level": r.rms_level,
            "peak_level": r.peak_level,
            "spectral_bandwidth": r.spectral_bandwidth,
            "spectral_rolloff": r.spectral_rolloff,
            "zcr": r.zcr,
            "created_at": r.created_at.isoformat(),
        }
        for r in records
    ]
