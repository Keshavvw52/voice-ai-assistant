from fastapi import APIRouter, HTTPException
import aiosqlite
import re

from services.auth_service import hash_password, verify_password, create_token

router = APIRouter()

DB_PATH = "voice_ai.db"
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def validate_credentials(email: str | None, password: str | None):
    normalized_email = (email or "").strip().lower()
    normalized_password = (password or "").strip()

    if not normalized_email or not normalized_password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    if not EMAIL_PATTERN.match(normalized_email):
        raise HTTPException(status_code=400, detail="Enter a valid email address")

    return normalized_email, normalized_password


@router.post("/signup")
async def signup(data: dict):
    email, password = validate_credentials(data.get("email"), data.get("password"))

    hashed = hash_password(password)

    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO users (email, password) VALUES (?, ?)",
                (email, hashed),
            )
            await db.commit()
        return {"message": "User created"}
    except:
        raise HTTPException(status_code=400, detail="User already exists")


@router.post("/login")
async def login(data: dict):
    email, password = validate_credentials(data.get("email"), data.get("password"))

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT password FROM users WHERE email = ?", (email,)
        )
        user = await cursor.fetchone()

    if not user or not verify_password(password, user[0]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token({"sub": email})
    return {"access_token": token}
