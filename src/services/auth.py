from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyCookie
import jwt
from jwt.exceptions import DecodeError
import os
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta, timezone
from src.services.methods import get_hash_password, verify_password, generate_uuid

logger = logging.getLogger(__name__)
logging.basicConfig(level="DEBUG")

load_dotenv()

AUTH_SECRET = os.getenv("AUTH_SECRET")

user_store = {
    "Jeson": "$argon2id$v=19$m=65536,t=3,p=4$AdVQJol6l5jqErC1bM8liw$KDlfh/lmk/uxemgFkmJjd/UI+O5Naww4irE3mu9UXvw"
}


def authorize(username: str, password: str) -> int | None:
    hash_password = user_store.get(username)
    if (not hash_password) or (not verify_password(password, hash_password)):
        return None
    return generate_uuid()

