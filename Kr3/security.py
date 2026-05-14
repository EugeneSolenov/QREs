from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import ExpiredSignatureError, InvalidTokenError
from passlib.context import CryptContext

from config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET_KEY
from database import find_user_by_username
from models import UserInDB


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(username, password):
    u = find_user_by_username(username)
    if u is None:
        return None
    if not verify_password(password, u["password"]):
        return None
    return u


def create_access_token(username, role):
    dt = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    d = {"sub": username, "role": role, "exp": dt}
    return jwt.encode(d, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def token_error(detail="Invalid or expired token"):
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    if credentials is None:
        raise token_error("Missing token")

    try:
        d = jwt.decode(
            credentials.credentials,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )
    except ExpiredSignatureError as exc:
        raise token_error("Token expired") from exc
    except InvalidTokenError as exc:
        raise token_error() from exc

    un = d.get("sub")
    if not isinstance(un, str) or not un:
        raise token_error()

    u = find_user_by_username(un)
    if u is None:
        raise token_error()

    return UserInDB(
        username=u["username"],
        hashed_password=u["password"],
        role=u["role"],
    )


def require_roles(*allowed_roles: str):
    def dep(current_user: UserInDB = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden",
            )
        return current_user

    return dep
