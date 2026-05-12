from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.auth.dependencies import get_current_user
from app.crud import fetch_all, insert, fetch_one, update, delete

router = APIRouter(prefix="/rooms", tags=["rooms"])

class RoomBase(BaseModel):
    name: str
    is_private: bool = True

class RoomCreate(RoomBase):
    is_group: bool = False

class RoomResponse(BaseModel):
    id: UUID
    name: str
    is_private: Optional[bool] = True
    active: Optional[bool] = True
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[RoomResponse])
async def list_rooms(current_user: dict = Depends(get_current_user)):
    # Note: Complex join queries still use database.pool.fetch in the original file
    # but I will try to stick to crud.py if possible or replicate the original logic
    from app import database
    q = """
        SELECT DISTINCT r.* 
        FROM rooms r
        LEFT JOIN room_members rm ON r.id = rm.room_id
        WHERE (rm.user_id = $1 OR r.is_private = False) AND r.active = True
        ORDER BY r.created_at DESC
    """
    rows = await database.pool.fetch(q, current_user["id"])
    return [dict(row) for row in rows]

@router.post("/", response_model=RoomResponse)
async def create_room(room: RoomCreate, current_user: dict = Depends(get_current_user)):
    new_room = await insert("rooms", {
        "name": room.name,
        "is_private": room.is_private
    })
    await insert("whiteboards", {
        "room_id": new_room["id"],
        "title": f"Whiteboard for {room.name}"
    })
    await insert("room_members", {
        "room_id": new_room["id"],
        "user_id": current_user["id"],
        "role": "admin"
    })
    return new_room

class MemberResponse(BaseModel):
    user_id: UUID
    username: str
    role: str

@router.get("/{room_id}/members", response_model=List[MemberResponse])
async def list_members(room_id: UUID, current_user: dict = Depends(get_current_user)):
    from app import database
    q = """
        SELECT rm.user_id, u.username, rm.role
        FROM room_members rm
        JOIN users u ON rm.user_id = u.id
        WHERE rm.room_id = $1
    """
    rows = await database.pool.fetch(q, room_id)
    return [dict(row) for row in rows]

@router.post("/{room_id}/members/{user_id}")
async def add_member(room_id: UUID, user_id: UUID, current_user: dict = Depends(get_current_user)):
    admin_check = await fetch_one("room_members", filters={"room_id": room_id, "user_id": current_user["id"], "role": "admin"})
    if not admin_check:
        raise HTTPException(status_code=403, detail="Only admins can add members")
    await insert("room_members", {"room_id": room_id, "user_id": user_id, "role": "member"})
    return {"status": "success"}

@router.delete("/{room_id}/members/{user_id}")
async def remove_member(room_id: UUID, user_id: UUID, current_user: dict = Depends(get_current_user)):
    admin_check = await fetch_one("room_members", filters={"room_id": room_id, "user_id": current_user["id"], "role": "admin"})
    if not admin_check:
        raise HTTPException(status_code=403, detail="Only admins can remove members")
    await delete("room_members", filters={"room_id": room_id, "user_id": user_id})
    return {"status": "success"}

@router.patch("/{room_id}/members/{user_id}")
async def update_member_role(room_id: UUID, user_id: UUID, role: str, current_user: dict = Depends(get_current_user)):
    admin_check = await fetch_one("room_members", filters={"room_id": room_id, "user_id": current_user["id"], "role": "admin"})
    if not admin_check:
        raise HTTPException(status_code=403, detail="Only admins can change roles")
    await update("room_members", data={"role": role}, filters={"room_id": room_id, "user_id": user_id})
    return {"status": "success"}

@router.delete("/{room_id}")
async def delete_room(room_id: UUID, current_user: dict = Depends(get_current_user)):
    admin_check = await fetch_one("room_members", filters={"room_id": room_id, "user_id": current_user["id"], "role": "admin"})
    if not admin_check:
        raise HTTPException(status_code=403, detail="Only admins can delete rooms")
    await update("rooms", data={"active": False}, filters={"id": room_id})
    return {"status": "success"}
