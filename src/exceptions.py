from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError
from librosa import LibrosaError


class BaseError(Exception):
    ...


class UserAlreadyExists(BaseError):
    ...


class NoAudioSegments(BaseError):
    ...


def setup_exceptions(app: FastAPI) -> None:
    @app.exception_handler(UserAlreadyExists)
    async def _(request: Request, exception: UserAlreadyExists):
        return JSONResponse(
            status_code=409,
            content={"detail": str(exception)}
        )

    @app.exception_handler(BaseError)
    async def _(request: Request, exception: BaseError):
        return JSONResponse(
            status_code=500,
            content={"detail": "Произошла непредвиденная ошибка. Попробуйте позже."}
        )

    @app.exception_handler(RedisError)
    async def _(request: Request, exception: RedisError):
        return JSONResponse(
            status_code=500,
            content={"detail": "Произошла непредвиденная ошибка. Попробуйте позже."}
        )

    @app.exception_handler(LibrosaError)
    async def _(request: Request, exception: LibrosaError):
        return JSONResponse(
            status_code=500,
            content={"detail": "Произошла непредвиденная ошибка при анализе данных, попробуйте позже."}
        )

    @app.exception_handler(NoAudioSegments)
    async def _(request: Request, exception: NoAudioSegments):
        return JSONResponse(
            status_code=404,
            content={"detail": "Звуки в аудио не обнаружены."}
        )
