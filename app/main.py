from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import connect, disconnect
from app.auth.router import router as auth_router
from app.messages.router import router as messages_router
from app.rooms.router import router as rooms_router
from app.whiteboard.router import router as whiteboard_router
from app.friends.router import router as friends_router
from typing import Dict, Set, List
import json

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect()
    yield
    await disconnect()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        # room_id -> set of websockets
        self.active_room_connections: Dict[str, Set[WebSocket]] = {}
        # user_id -> websocket
        self.active_user_connections: Dict[str, WebSocket] = {}
        self.active_user_rooms: Dict[str, str] = {}

    async def connect_room(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_room_connections:
            self.active_room_connections[room_id] = set()
        self.active_room_connections[room_id].add(websocket)

    def disconnect_room(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_room_connections:
            if websocket in self.active_room_connections[room_id]:
                self.active_room_connections[room_id].remove(websocket)
            if not self.active_room_connections[room_id]:
                del self.active_room_connections[room_id]

    async def connect_user(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_user_connections[user_id] = websocket

    def disconnect_user(self, user_id: str):
        if user_id in self.active_user_connections:
            del self.active_user_connections[user_id]
        if user_id in self.active_user_rooms:
            del self.active_user_rooms[user_id]

    async def set_user_room(self, user_id: str, room_id: str):
        self.active_user_rooms[user_id] = room_id

    async def broadcast_room(self, message: dict, room_id: str, exclude: WebSocket = None):
        if room_id in self.active_room_connections:
            for connection in self.active_room_connections[room_id]:
                if connection != exclude:
                    try:
                        await connection.send_json(message)
                    except:
                        pass

    async def broadcast_chat_to_room(self, message: dict, room_id: str, exclude_user_id: str = None):
        # Broadcast to everyone currently viewing the room via their chat socket
        for uid, rid in self.active_user_rooms.items():
            if rid == room_id and uid != exclude_user_id:
                await self.send_to_user(message, uid)

    async def send_to_user(self, message: dict, user_id: str):
        if user_id in self.active_user_connections:
            try:
                await self.active_user_connections[user_id].send_json(message)
            except:
                pass

manager = ConnectionManager()

@app.websocket("/ws/{room_id}")
async def websocket_room_endpoint(websocket: WebSocket, room_id: str):
    await manager.connect_room(websocket, room_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await manager.broadcast_room(message, room_id, exclude=websocket)
    except WebSocketDisconnect:
        manager.disconnect_room(websocket, room_id)

@app.websocket("/ws/chat/{user_id}")
async def websocket_chat_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect_user(websocket, user_id)
    from app.crud import database
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle room presence
            if message.get("type") == "join_room":
                await manager.set_user_room(user_id, message.get("room_id"))
                continue

            # format: {"type": "chat", "receiver_id": "...", "room_id": "...", "data": {...}}
            if message.get("type") == "chat":
                if message.get("room_id"):
                    # Broadcast to everyone currently in the room (Active Presence)
                    await manager.broadcast_chat_to_room(message, message["room_id"], exclude_user_id=user_id)
                    
                    # FALLBACK/PERSISTENCE: Also send to all formal room members who might be online but in different rooms
                    q = "SELECT user_id FROM room_members WHERE room_id = $1"
                    members = await database.pool.fetch(q, message["room_id"])
                    for member in members:
                        mid = str(member["user_id"])
                        # Don't send twice if they are already in the room (broadcast_chat_to_room handled them)
                        # and don't send to self
                        if mid != user_id and mid not in manager.active_user_rooms:
                            await manager.send_to_user(message, mid)
                elif message.get("receiver_id"):
                    await manager.send_to_user(message, message["receiver_id"])
    except WebSocketDisconnect:
        manager.disconnect_user(user_id)

app.include_router(auth_router)
app.include_router(messages_router)
app.include_router(rooms_router)
app.include_router(whiteboard_router)
app.include_router(friends_router)