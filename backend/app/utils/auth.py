import secrets
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import bcrypt


TOKEN_SIZE = 32

DELTA_DAYS = 3

ENCODING = 'utf-8'


def generate_session_token() -> str:
    return secrets.token_hex(TOKEN_SIZE)


def generate_expiration_datetime() -> datetime:
    return datetime.utcnow() + timedelta(days=DELTA_DAYS)


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(ENCODING), salt)
    return hashed.decode(ENCODING)


def check_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        password.encode(ENCODING), hashed_password.encode(ENCODING)
    )
