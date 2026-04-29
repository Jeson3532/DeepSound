from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError


class BaseError(Exception):
    ...


class UserAlreadyExists(BaseError):
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
