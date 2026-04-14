import hashlib
from jose import jwt
from datetime import datetime, timedelta

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain, hashed):
    return hash_password(plain) == hashed


def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=2)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)