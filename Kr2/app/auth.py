import os
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4
from itsdangerous import BadSignature, Signer
from app.models import UserProfile
SESSION_COOKIE_NAME = "session_token"
SESSION_TTL_SECONDS = 300
SESSION_REFRESH_AFTER_SECONDS = 180
SECRET_KEY = os.getenv("APP_SECRET_KEY", "dev-secret-key-change-me")
@dataclass
class SessionData:
    user_id: str
    last_activity: int
class UnauthorizedError(Exception):
    pass
class InvalidCredentialsError(Exception):
    pass
class InvalidSessionError(Exception):
    pass
class SessionExpiredError(Exception):
    pass
signer = Signer(SECRET_KEY)
users = {
    "user123": {
        "password": "password123",
        "user_id": str(uuid4()),
        "email": "user123@example.com",
        "full_name": "Test User 123",
    },
    "alice": {
        "password": "alicepass",
        "user_id": str(uuid4()),
        "email": "alice@example.com",
        "full_name": "Alice Johnson",
    },
}
USER_PROFILES = {}
for n, r in users.items():
    USER_PROFILES[r["user_id"]] = UserProfile(
        user_id=r["user_id"],
        username=n,
        email=r["email"],
        full_name=r["full_name"],
    )
def current_timestamp():
    return int(datetime.now(timezone.utc).timestamp())
def authenticate_user(username, password):
    r = users.get(username)
    if not r or r["password"] != password:
        raise InvalidCredentialsError
    return USER_PROFILES[r["user_id"]]
def create_session_token(user_id, last_activity=None):
    t = current_timestamp() if last_activity is None else last_activity
    s = f"{user_id}.{t}"
    return signer.sign(s.encode("utf-8")).decode("utf-8")
def parse_session_token(token):
    try:
        s = signer.unsign(token).decode("utf-8")
    except BadSignature as e:
        raise InvalidSessionError from e
    try:
        uid, tx = s.rsplit(".", maxsplit=1)
        t = int(tx)
    except ValueError as e:
        raise InvalidSessionError from e
    if uid not in USER_PROFILES:
        raise InvalidSessionError
    age = current_timestamp() - t
    if age > SESSION_TTL_SECONDS:
        raise SessionExpiredError
    if age < 0:
        raise InvalidSessionError
    return SessionData(user_id=uid, last_activity=t)
def should_refresh_session(last_activity):
    age = current_timestamp() - last_activity
    return SESSION_REFRESH_AFTER_SECONDS <= age <= SESSION_TTL_SECONDS
