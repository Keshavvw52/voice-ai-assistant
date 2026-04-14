import sqlite3
from fastapi import APIRouter, HTTPException, Depends
import re

from models.database import get_db
from services.auth_service import (
    create_token,
    hash_password,
    password_needs_rehash,
    verify_password,
)

router = APIRouter()

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
async def signup(data: dict, db=Depends(get_db)):
    email, password = validate_credentials(data.get("email"), data.get("password"))

    hashed = hash_password(password)

    try:
        await db.execute(
            "INSERT INTO users (email, password) VALUES (?, ?)",
            (email, hashed),
        )
        await db.commit()
        return {"message": "User created"}

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=400,
            detail="User already exists"
        )


@router.post("/login")
async def login(data: dict, db=Depends(get_db)):
    email, password = validate_credentials(data.get("email"), data.get("password"))

    cursor = await db.execute(
        "SELECT id, email, password FROM users WHERE email = ?", (email,)
    )
    user = await cursor.fetchone()

    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if password_needs_rehash(user["password"]):
        await db.execute(
            "UPDATE users SET password = ? WHERE id = ?",
            (hash_password(password), user["id"]),
        )
        await db.commit()

    token = create_token({"sub": user["email"], "user_id": user["id"]})
    return {"access_token": token}
