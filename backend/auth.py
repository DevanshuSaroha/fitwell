import os, hmac, hashlib, secrets, time
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from models import get_db, User

SECRET = os.environ.get("SECRET_KEY", "dev-secret-change-me")
bearer = HTTPBearer(auto_error=False)


def _hash(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    return f"{salt}${_hash(password, salt)}"


def verify_password(password: str, stored: str) -> bool:
    salt, digest = stored.split("$")
    return hmac.compare_digest(_hash(password, salt), digest)


def make_token(user_id: int) -> str:
    return jwt.encode({"sub": str(user_id), "exp": int(time.time()) + 7 * 86400}, SECRET, algorithm="HS256")


def current_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer),
                 db: Session = Depends(get_db)) -> User:
    if not creds:
        raise HTTPException(401, "Please log in first.")
    try:
        uid = int(jwt.decode(creds.credentials, SECRET, algorithms=["HS256"])["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(401, "Your session has expired. Please log in again.")
    user = db.get(User, uid)
    if not user:
        raise HTTPException(401, "Account not found.")
    return user
