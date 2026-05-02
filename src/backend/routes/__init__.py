from fastapi import APIRouter
from src.backend.routes.auth import router as auth_router
from src.backend.routes.audio import router as audio_router
routers = [v for v in list(globals().values()) if type(v) is APIRouter]