import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
from pathlib import Path
from contextlib import asynccontextmanager
from src.services.database.redis.engine import RedisManager
from src.backend.routes import routers
from src.exceptions import setup_exceptions
from src.services.audio.service import AudioService

root_path = Path(os.getenv("PYTHONPATH"))
app_path = root_path / 'src' / 'backend' / 'entry'
relative_path = '.'.join(app_path.relative_to(root_path).parts)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Импорт роутеров
    for router in routers:
        app.include_router(router)

    # Redis
    redis_manager = RedisManager()
    await redis_manager.initialize()
    app.state.redis = redis_manager.client
    # ML
    app.state.audio_service = AudioService()

    yield

    # Redis
    await redis_manager.close()


app = FastAPI(title="API DeepSound", version='1.0.0', lifespan=lifespan)
setup_exceptions(app)  # handling exc

if __name__ == '__main__':
    uvicorn.run(f"{relative_path}:app", host='localhost', port=5000, reload=True)
