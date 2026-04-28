from fastapi import APIRouter
from src.backend.routes.auth import router as auth_router

routers = [v for v in list(globals().values()) if type(v) is APIRouter]