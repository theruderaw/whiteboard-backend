from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.auth.dependencies import get_current_user
from app.crud import fetch_all, insert, database, fetch_one, delete, update

router = APIRouter(prefix="/friends", tags=["friends"])

class FriendResponse(BaseModel):
    id: UUID
    username: str
    status: str
    created_at: datetime

@router.get("/", response_model=List[FriendResponse])
async def list_friends(current_user: dict = Depends(get_current_user)):
    from app import database
    q = """
        SELECT f.id as friendship_id, u.id, u.username, f.status, f.created_at
        FROM friendships f
        JOIN users u ON (f.friend_id = u.id AND f.user_id = $1) 
                     OR (f.user_id = u.id AND f.friend_id = $1)
        WHERE f.status = 'accepted' AND u.id != $1
    """
    rows = await database.pool.fetch(q, current_user["id"])
    return [
        {"id": row["id"], "username": row["username"], "status": row["status"], "created_at": row["created_at"]}
        for row in rows
    ]

@router.get("/requests", response_model=List[FriendResponse])
async def list_friend_requests(current_user: dict = Depends(get_current_user)):
    from app import database
    q = """
        SELECT f.id as friendship_id, u.id, u.username, f.status, f.created_at
        FROM friendships f
        JOIN users u ON f.user_id = u.id
        WHERE f.friend_id = $1 AND f.status = 'pending'
    """
    rows = await database.pool.fetch(q, current_user["id"])
    return [
        {"id": row["id"], "username": row["username"], "status": row["status"], "created_at": row["created_at"]}
        for row in rows
    ]

@router.post("/request/{friend_id}")
async def send_friend_request(friend_id: UUID, current_user: dict = Depends(get_current_user)):
    if friend_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot add yourself as a friend")
    receiver = await fetch_one("users", filters={"id": friend_id})
    if not receiver:
        raise HTTPException(status_code=404, detail="User not found")
    
    from app import database
    existing = await database.pool.fetchrow(
        "SELECT id FROM friendships WHERE (user_id = $1 AND friend_id = $2) OR (user_id = $2 AND friend_id = $1)",
        current_user["id"], friend_id
    )
    if existing:
        raise HTTPException(status_code=400, detail="Friendship already exists or request pending")
    
    await insert("friendships", {"user_id": current_user["id"], "friend_id": friend_id, "status": "pending"})
    return {"message": "Friend request sent"}

@router.post("/accept/{friend_id}")
async def accept_friend_request(friend_id: UUID, current_user: dict = Depends(get_current_user)):
    row = await update("friendships", data={"status": "accepted"}, filters={"user_id": friend_id, "friend_id": current_user["id"], "status": "pending"})
    if not row:
        raise HTTPException(status_code=404, detail="Friend request not found")
    return {"message": "Friend request accepted"}

@router.delete("/{friend_id}")
async def remove_friend(friend_id: UUID, current_user: dict = Depends(get_current_user)):
    from app import database
    q = "DELETE FROM friendships WHERE (user_id = $1 AND friend_id = $2) OR (user_id = $2 AND friend_id = $1)"
    await database.pool.execute(q, current_user["id"], friend_id)
    return {"message": "Friend removed"}

@router.post("/request/by-username/{username}")
async def send_friend_request_by_username(username: str, current_user: dict = Depends(get_current_user)):
    receiver = await fetch_one("users", filters={"username": username})
    if not receiver:
        raise HTTPException(status_code=404, detail="User not found")
    if receiver["id"] == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot add yourself as a friend")
    
    from app import database
    existing = await database.pool.fetchrow(
        "SELECT id FROM friendships WHERE (user_id = $1 AND friend_id = $2) OR (user_id = $2 AND friend_id = $1)",
        current_user["id"], receiver["id"]
    )
    if existing:
        raise HTTPException(status_code=400, detail="Friendship already exists or request pending")
    
    await insert("friendships", {"user_id": current_user["id"], "friend_id": receiver["id"], "status": "pending"})
    return {"message": "Friend request sent"}
