from pwdlib import PasswordHash
from pwdlib.exceptions import HasherNotAvailable, UnknownHashError
import logging
import secrets
import string

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR)

pwd = PasswordHash.recommended()
dictionary = string.ascii_letters + string.digits


def generate_uuid(length: int = 16):
    return ''.join(secrets.choice(dictionary) for _ in range(length))


def get_hash_password(password: str) -> str:
    try:
        return pwd.hash(password)
    except HasherNotAvailable as e:
        logger.error(f"Ошибка {e.__class__.__name__} при хешировании: {e}")
    except Exception as e:
        logger.error(f"Общая ошибка {e.__class__.__name__} при хешировании: {e}")


def verify_password(password: str, hash_password: str) -> bool:
    try:
        return pwd.verify(password, hash_password)
    except UnknownHashError as e:
        logger.error(f"Ошибка {e.__class__.__name__} при верификации пароля: {e}")
        return False
    except Exception as e:
        logger.error(f"Общая ошибка {e.__class__.__name__} при верификации пароля: {e}")
        return False


