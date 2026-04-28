import uvicorn
from fastapi import FastAPI
import os
from pathlib import Path
from contextlib import asynccontextmanager
from src.service.database.redis.engine import RedisManager
from src.backend.routes import routers

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

    yield

    # Redis
    await redis_manager.close()


app = FastAPI(title="API DeepSound", version='1.0.0', lifespan=lifespan)

if __name__ == '__main__':
    uvicorn.run(f"{relative_path}:app", host='localhost', port=5000, reload=True)
