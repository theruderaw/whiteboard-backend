from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt
from app.config import JWT_SECRET, JWT_REFRESH_SECRET, JWT_RESET_SECRET
import hashlib

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain):
    return pwd.hash(plain)

def verify_password(plain, hashed):
    return pwd.verify(plain, hashed)

def make_token(payload, secret, minutes=None, days=None):
    exp = datetime.now(timezone.utc)
    if minutes: exp += timedelta(minutes=minutes)
    if days:    exp += timedelta(days=days)
    return jwt.encode({**payload, "exp": exp}, secret, algorithm="HS256")

def decode_token(token, secret):
    return jwt.decode(token, secret, algorithms=["HS256"])

def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()

def make_access_token(user_id, email):
    return make_token({"sub": str(user_id), "email": email}, JWT_SECRET, minutes=15)

def make_refresh_token(user_id):
    return make_token({"sub": str(user_id)}, JWT_REFRESH_SECRET, days=7)

def make_reset_token(user_id):
    return make_token({"sub": str(user_id)}, JWT_RESET_SECRET, minutes=30)