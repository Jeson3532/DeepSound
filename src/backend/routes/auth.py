from fastapi import APIRouter, Body, Request, HTTPException
from src.service.auth import authorize
from src.backend.schemas.base.auth import UserLogin, UserRegister
from src.backend.schemas.response.auth import UserRegisterResponse
from src.service.database.redis.service import RedisService

router = APIRouter(prefix="/auth", tags=["Authorize"])


@router.post("/login")
async def login(request: Request, body: UserLogin = Body()):
    username = body.username
    session = authorize(username, body.password)
    if not session:
        raise HTTPException(status_code=401, detail="Неверные данные")

    redis_client = request.app.state.redis
    response = await RedisService(redis_client).create_session(session, username)
    if not response:
        raise HTTPException(status_code=500, detail="Произошла непредвиденная ошибка")
    return {
        "status_code": 200,
        "session_id": session
    }


@router.post("/register", response_model=UserRegisterResponse)
async def register(request: Request, body: UserRegister = Body()):
    username = body.username
    password, repeat_password = body.password, body.repeat_password
    email = body.email
    return {
        "id": 1,
        "username": username,
        "password": password,
        "email": email
    }
