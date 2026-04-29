from fastapi import APIRouter, Body, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.auth import authorize
from src.schemas.base.auth import UserLogin, UserRegister
from src.schemas.response.auth import UserRegisterResponse, UserRegisterResponseSuccess
from src.services.database.redis.service import RedisService
from src.services.database.pg.engine import get_session
from src.services.database.pg.service import DatabaseService
from src.services.methods import generate_uuid

router = APIRouter(prefix="/auth", tags=["Authorize"])


@router.post("/login")
async def login(request: Request, body: UserLogin = Body()):
    username = body.username
    session_id = authorize(username, body.password)
    if not session_id:
        raise HTTPException(status_code=401, detail="Неверные данные")

    redis_client = request.app.state.redis
    await RedisService(redis_client).create_session(session_id, username)
    return JSONResponse(status_code=200, content={"session_id": session_id})


@router.post("/register", response_model=UserRegisterResponseSuccess)
async def register(request: Request, creds: UserRegister = Body(), session: AsyncSession = Depends(get_session)):
    db = DatabaseService(session=session)
    redis_client = request.app.state.redis
    try:
        user = await db.users.add_user(creds)

        await db.commit()
        await session.refresh(user)

        uuid = generate_uuid()
        user_model = UserRegisterResponse.model_validate(user).model_dump()
        await RedisService(redis_client).create_session(uuid, creds.username)

        return JSONResponse(status_code=200, content=user_model | {"session_id": uuid})
    except Exception:
        await db.rollback()
        raise
