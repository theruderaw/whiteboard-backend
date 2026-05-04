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

    async def broadcast_room(self, message: dict, room_id: str, exclude: WebSocket = None):
        if room_id in self.active_room_connections:
            for connection in self.active_room_connections[room_id]:
                if connection != exclude:
                    try:
                        await connection.send_json(message)
                    except:
                        pass

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
    try:
        while True:
            # We mostly use this to receive messages for the user
            # But the user could also send 1-to-1 messages here
            data = await websocket.receive_text()
            message = json.loads(data)
            # format: {"type": "chat", "receiver_id": "...", "data": {...}}
            if message.get("type") == "chat":
                await manager.send_to_user(message, message["receiver_id"])
    except WebSocketDisconnect:
        manager.disconnect_user(user_id)

app.include_router(auth_router)
app.include_router(messages_router)
app.include_router(rooms_router)
app.include_router(whiteboard_router)
app.include_router(friends_router)