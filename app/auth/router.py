from fastapi import APIRouter, HTTPException, Cookie
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.auth.service import (
    verify_password, hash_token,
    make_access_token, make_refresh_token, make_reset_token,
    decode_token, JWT_REFRESH_SECRET
)
from app.auth.dependencies import get_current_user
from app.config import ENV
from app.crud import fetch_one, insert, update, delete

from fastapi import Depends

router = APIRouter(prefix="/auth")

# ── request models ───────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str

# ── response models ──────────────────────────────────────────────
class AccessTokenResponse(BaseModel):
    access_token: str

class ResetTokenResponse(BaseModel):
    reset_token: str

class UserResponse(BaseModel):
    id: str

    username: str
    active: bool

# ── routes ───────────────────────────────────────────────────────
@router.post("/login", response_model=AccessTokenResponse)
async def login(body: LoginRequest):
    user = await fetch_one("users", {"username": body.username})
    if not user or not user["active"] or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(401, "Invalid credentials")

    access  = make_access_token(user["id"], user["username"])
    refresh = make_refresh_token(user["id"])

    await insert("refresh_tokens", {"user_id": user["id"], "token_hash": hash_token(refresh)})

    response = JSONResponse(content={"access_token": access})
    
    is_prod = ENV == "production"
    response.set_cookie(
        "refresh_token", 
        refresh, 
        httponly=True, 
        samesite="strict" if is_prod else "lax",
        secure=is_prod
    )
    return response

@router.get("/me", response_model=UserResponse)
async def me(current_user: dict = Depends(get_current_user)):
    user_dict = dict(current_user)
    user_dict["id"] = str(user_dict["id"])
    return user_dict

@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(refresh_token: str = Cookie(None)):
    if not refresh_token:
        raise HTTPException(401, "No refresh token")
    try:
        payload = decode_token(refresh_token, JWT_REFRESH_SECRET)
    except:
        raise HTTPException(401, "Invalid token")

    row = await fetch_one("refresh_tokens", {"user_id": payload["sub"], "token_hash": hash_token(refresh_token)})
    if not row:
        raise HTTPException(401, "Token revoked")

    user = await fetch_one("users", {"id": payload["sub"]})
    if not user:
        raise HTTPException(404, "User not found")

    new_refresh = make_refresh_token(user["id"])
    await update("refresh_tokens", {"token_hash": hash_token(new_refresh)}, {"id": row["id"]})

    response = JSONResponse(content={"access_token": make_access_token(user["id"], user["username"])})
    
    is_prod = ENV == "production"
    response.set_cookie(
        "refresh_token", 
        new_refresh, 
        httponly=True, 
        samesite="strict" if is_prod else "lax",
        secure=is_prod
    )
    return response

@router.post("/reset", response_model=ResetTokenResponse)
async def reset(refresh_token: str = Cookie(None)):
    if not refresh_token:
        raise HTTPException(401, "No refresh token")
    try:
        payload = decode_token(refresh_token, JWT_REFRESH_SECRET)
    except:
        raise HTTPException(401, "Invalid token")

    user = await fetch_one("users", {"id": payload["sub"]})
    if not user:
        raise HTTPException(404, "User not found")

    return ResetTokenResponse(reset_token=make_reset_token(user["id"]))

@router.post("/logout")
async def logout(refresh_token: str = Cookie(None)):
    response = JSONResponse(content={"message": "Logged out"})
    response.delete_cookie("refresh_token")
    
    if refresh_token:
        await delete("refresh_tokens", {"token_hash": hash_token(refresh_token)})
        
    return response
@router.get("/users")
async def get_users(current_user: dict = Depends(get_current_user)):
    q = "SELECT id, username FROM users WHERE id != $1"
    from app.crud import database
    rows = await database.pool.fetch(q, current_user["id"])
    return [{"id": str(row["id"]), "username": row["username"]} for row in rows]

@router.get("/users/search")
async def search_users(q: str, current_user: dict = Depends(get_current_user)):
    from app.crud import database
    query = "SELECT id, username FROM users WHERE username ILIKE $1 AND id != $2 LIMIT 10"
    rows = await database.pool.fetch(query, f"%{q}%", current_user["id"])
    return [{"id": str(row["id"]), "username": row["username"]} for row in rows]
