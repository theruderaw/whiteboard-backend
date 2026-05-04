from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.auth.dependencies import get_current_user
from app.crud import fetch_all, insert, database, fetch_one, delete

router = APIRouter(prefix="/friends", tags=["friends"])

class FriendResponse(BaseModel):
    id: UUID
    username: str
    status: str
    created_at: datetime

@router.get("/", response_model=List[FriendResponse])
async def list_friends(current_user: dict = Depends(get_current_user)):
    # Fetch friends where status is 'accepted'
    # We need to join with users table to get usernames
    q = """
        SELECT f.id as friendship_id, u.id, u.username, f.status, f.created_at
        FROM friendships f
        JOIN users u ON (f.friend_id = u.id AND f.user_id = $1) 
                     OR (f.user_id = u.id AND f.friend_id = $1)
        WHERE f.status = 'accepted' AND u.id != $1
    """
    rows = await database.pool.fetch(q, current_user["id"])
    return [
        {
            "id": row["id"],
            "username": row["username"],
            "status": row["status"],
            "created_at": row["created_at"]
        }
        for row in rows
    ]

@router.get("/requests", response_model=List[FriendResponse])
async def list_friend_requests(current_user: dict = Depends(get_current_user)):
    # Fetch pending requests where current_user is the recipient (friend_id)
    q = """
        SELECT f.id as friendship_id, u.id, u.username, f.status, f.created_at
        FROM friendships f
        JOIN users u ON f.user_id = u.id
        WHERE f.friend_id = $1 AND f.status = 'pending'
    """
    rows = await database.pool.fetch(q, current_user["id"])
    return [
        {
            "id": row["id"],
            "username": row["username"],
            "status": row["status"],
            "created_at": row["created_at"]
        }
        for row in rows
    ]

@router.post("/request/{friend_id}")
async def send_friend_request(friend_id: UUID, current_user: dict = Depends(get_current_user)):
    if friend_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot add yourself as a friend")
    
    # Check if receiver exists
    receiver = await database.pool.fetchrow("SELECT id FROM users WHERE id = $1", friend_id)
    if not receiver:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if friendship already exists
    existing = await database.pool.fetchrow(
        "SELECT id FROM friendships WHERE (user_id = $1 AND friend_id = $2) OR (user_id = $2 AND friend_id = $1)",
        current_user["id"], friend_id
    )
    if existing:
        raise HTTPException(status_code=400, detail="Friendship already exists or request pending")
    
    await insert("friendships", {
        "user_id": current_user["id"],
        "friend_id": friend_id,
        "status": "pending"
    })
    return {"message": "Friend request sent"}

@router.post("/accept/{friend_id}")
async def accept_friend_request(friend_id: UUID, current_user: dict = Depends(get_current_user)):
    # Update status to 'accepted' where current_user is friend_id
    q = "UPDATE friendships SET status = 'accepted' WHERE user_id = $1 AND friend_id = $2 AND status = 'pending' RETURNING id"
    row = await database.pool.fetchrow(q, friend_id, current_user["id"])
    if not row:
        raise HTTPException(status_code=404, detail="Friend request not found")
    return {"message": "Friend request accepted"}

@router.delete("/{friend_id}")
async def remove_friend(friend_id: UUID, current_user: dict = Depends(get_current_user)):
    q = "DELETE FROM friendships WHERE (user_id = $1 AND friend_id = $2) OR (user_id = $2 AND friend_id = $1)"
    await database.pool.execute(q, current_user["id"], friend_id)
    return {"message": "Friend removed"}
