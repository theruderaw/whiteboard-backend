from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.auth.dependencies import get_current_user
from app.crud import fetch_all, insert, database, fetch_one

router = APIRouter(prefix="/rooms", tags=["rooms"])

class RoomBase(BaseModel):
    name: str
    is_private: bool = True

class RoomCreate(RoomBase):
    pass

class RoomResponse(RoomBase):
    id: UUID
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[RoomResponse])
async def list_rooms(current_user: dict = Depends(get_current_user)):
    # List rooms the user is a member of or all public rooms
    # For now, let's just list all active rooms for simplicity
    rooms = await fetch_all("rooms", filters={"active": True}, order_by="created_at DESC")
    return rooms

@router.post("/", response_model=RoomResponse)
async def create_room(room: RoomCreate, current_user: dict = Depends(get_current_user)):
    new_room = await insert("rooms", {
        "name": room.name,
        "is_private": room.is_private
    })
    
    # Auto-create a whiteboard for the new room
    await insert("whiteboards", {
        "room_id": new_room["id"],
        "title": f"Whiteboard for {room.name}"
    })
    
    # Add creator as member
    await insert("room_members", {
        "room_id": new_room["id"],
        "user_id": current_user["id"],
        "role": "admin"
    })
    
    return new_room

@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(room_id: UUID, current_user: dict = Depends(get_current_user)):
    room = await fetch_one("rooms", filters={"id": room_id})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room
