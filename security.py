from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from .config import settings

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(p: str) -> str: return pwd.hash(p)
def verify_password(p: str, h: str) -> bool: return pwd.verify(p, h)

def _make(sub: str, kind: str, minutes: int) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": sub, "kind": kind, "iat": int(now.timestamp()),
         "exp": int((now + timedelta(minutes=minutes)).timestamp())},
        settings.jwt_secret, algorithm=settings.jwt_algorithm)

def make_access(uid: str) -> str: return _make(uid, "access", settings.access_token_minutes)
def make_refresh(uid: str) -> str: return _make(uid, "refresh", settings.refresh_token_days * 1440)

def decode(token: str, expect_kind: str) -> str | None:
    try:
        data = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if data.get("kind") != expect_kind: return None
        return data.get("sub")
    except JWTError:
        return None