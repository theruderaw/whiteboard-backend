from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from uuid import UUID
from datetime import datetime
from app.auth.dependencies import get_current_user
from app.crud import fetch_all, insert, database

router = APIRouter(prefix="/messages", tags=["messages"])

class MessageCreate(BaseModel):
    receiver_id: UUID
    content: str

class MessageResponse(BaseModel):
    id: UUID
    sender_id: UUID
    receiver_id: UUID
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True

@router.post("/", response_model=MessageResponse)
async def send_message(msg: MessageCreate, current_user: dict = Depends(get_current_user)):
    # Check if receiver exists
    receiver = await database.pool.fetchrow("SELECT id FROM users WHERE id = $1", msg.receiver_id)
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")
    
    new_msg = await insert("messages", {
        "sender_id": current_user["id"],
        "receiver_id": msg.receiver_id,
        "content": msg.content
    })
    
    return {
        "id": new_msg["id"],
        "sender_id": new_msg["sender_id"],
        "receiver_id": new_msg["receiver_id"],
        "content": new_msg["content"],
        "timestamp": new_msg["timestamp"]
    }

@router.get("/{other_user_id}", response_model=List[MessageResponse])
async def get_chat_history(other_user_id: UUID, current_user: dict = Depends(get_current_user)):
    # Fetch messages between current_user and other_user_id in chronological order
    q = """
        SELECT * FROM messages 
        WHERE (sender_id = $1 AND receiver_id = $2) 
           OR (sender_id = $2 AND receiver_id = $1)
        ORDER BY timestamp ASC
    """
    rows = await database.pool.fetch(q, current_user["id"], other_user_id)
    
    return [
        {
            "id": row["id"],
            "sender_id": row["sender_id"],
            "receiver_id": row["receiver_id"],
            "content": row["content"],
            "timestamp": row["timestamp"]
        }
        for row in rows
    ]
