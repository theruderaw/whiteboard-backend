from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.auth.dependencies import get_current_user
from app.crud import fetch_all, insert, database, fetch_one

router = APIRouter(prefix="/whiteboard", tags=["whiteboard"])

class StrokeCreate(BaseModel):
    whiteboard_id: UUID
    type: str  # 'stroke', 'shape', 'text', 'erase'
    data: dict

class StrokeResponse(BaseModel):
    id: UUID
    whiteboard_id: UUID
    user_id: Optional[UUID]
    type: str
    data: dict
    created_at: datetime

    class Config:
        from_attributes = True

class WhiteboardResponse(BaseModel):
    id: UUID
    room_id: UUID
    title: str
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/room/{room_id}", response_model=WhiteboardResponse)
async def get_room_whiteboard(room_id: UUID, current_user: dict = Depends(get_current_user)):
    # Get the primary whiteboard for a room
    wb = await fetch_one("whiteboards", filters={"room_id": room_id}, order_by="position ASC")
    if not wb:
        # If no whiteboard exists, create one
        wb = await insert("whiteboards", {
            "room_id": room_id,
            "title": "Default Whiteboard"
        })
    return wb

@router.get("/{whiteboard_id}/strokes", response_model=List[StrokeResponse])
async def get_strokes(whiteboard_id: UUID, current_user: dict = Depends(get_current_user)):
    import json
    rows = await fetch_all("strokes", filters={"whiteboard_id": whiteboard_id}, order_by="created_at ASC")
    
    strokes = []
    for row in rows:
        stroke = dict(row)
        if isinstance(stroke["data"], str):
            stroke["data"] = json.loads(stroke["data"])
        strokes.append(stroke)
    return strokes

@router.post("/strokes", response_model=StrokeResponse)
async def save_stroke(stroke: StrokeCreate, current_user: dict = Depends(get_current_user)):
    # Validate type
    if stroke.type not in ['stroke', 'shape', 'text', 'erase']:
        raise HTTPException(status_code=400, detail="Invalid stroke type")
    
    import json
    new_stroke = await insert("strokes", {
        "whiteboard_id": stroke.whiteboard_id,
        "user_id": current_user["id"],
        "type": stroke.type,
        "data": json.dumps(stroke.data)
    })
    
    # Parse data back to dict for the response model
    res = dict(new_stroke)
    if isinstance(res["data"], str):
        res["data"] = json.loads(res["data"])
    return res

@router.delete("/{whiteboard_id}/clear")
async def clear_whiteboard(whiteboard_id: UUID, current_user: dict = Depends(get_current_user)):
    # Get room_id for this whiteboard
    wb = await database.pool.fetchrow("SELECT room_id FROM whiteboards WHERE id = $1", whiteboard_id)
    if not wb:
        raise HTTPException(status_code=404, detail="Whiteboard not found")
    
    # Check if user is admin in that room
    admin_check = await database.pool.fetchrow(
        "SELECT 1 FROM room_members WHERE room_id = $1 AND user_id = $2 AND role = 'admin'",
        wb["room_id"], current_user["id"]
    )
    if not admin_check:
        raise HTTPException(status_code=403, detail="Only admins can clear the whiteboard")

    await database.pool.execute("DELETE FROM strokes WHERE whiteboard_id = $1", whiteboard_id)
    return {"status": "cleared"}
