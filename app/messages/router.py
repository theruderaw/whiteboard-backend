from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.auth.dependencies import get_current_user
from app.crud import fetch_all, insert, database

router = APIRouter(prefix="/messages", tags=["messages"])

class MessageCreate(BaseModel):
    content: str
    receiver_id: Optional[UUID] = None
    room_id: Optional[UUID] = None

class MessageResponse(BaseModel):
    id: UUID
    sender_id: UUID
    sender_username: Optional[str] = None
    receiver_id: Optional[UUID] = None
    room_id: Optional[UUID] = None
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True

@router.post("/", response_model=MessageResponse)
async def send_message(msg: MessageCreate, current_user: dict = Depends(get_current_user)):
    if msg.room_id:
        new_msg = await insert("messages", {
            "sender_id": current_user["id"],
            "room_id": msg.room_id,
            "content": msg.content
        })
    elif msg.receiver_id:
        new_msg = await insert("messages", {
            "sender_id": current_user["id"],
            "receiver_id": msg.receiver_id,
            "content": msg.content
        })
    else:
        raise HTTPException(status_code=400, detail="Either receiver_id or room_id must be provided")
    
    return {
        "id": new_msg["id"],
        "sender_id": new_msg["sender_id"],
        "receiver_id": new_msg.get("receiver_id"),
        "room_id": new_msg.get("room_id"),
        "content": new_msg["content"],
        "timestamp": new_msg["timestamp"]
    }

@router.get("/{id}", response_model=List[MessageResponse])
async def get_chat_history(
    id: UUID, 
    is_room: bool = Query(False),
    current_user: dict = Depends(get_current_user)
):
    if is_room:
        q = """
            SELECT m.*, u.username as sender_username 
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE m.room_id = $1
            ORDER BY m.timestamp ASC
        """
        rows = await database.pool.fetch(q, id)
    else:
        q = """
            SELECT m.*, u.username as sender_username 
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE (m.sender_id = $1 AND m.receiver_id = $2) 
               OR (m.sender_id = $2 AND m.receiver_id = $1)
            ORDER BY m.timestamp ASC
        """
        rows = await database.pool.fetch(q, current_user["id"], id)
    
    return [dict(row) for row in rows]
