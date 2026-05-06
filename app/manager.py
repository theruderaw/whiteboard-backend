from fastapi import WebSocket
from typing import Dict, Set, List
import json

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
        self.active_user_connections[str(user_id)] = websocket

    def disconnect_user(self, user_id: str):
        uid = str(user_id)
        if uid in self.active_user_connections:
            del self.active_user_connections[uid]
        if uid in self.active_user_rooms:
            del self.active_user_rooms[uid]

    async def set_user_room(self, user_id: str, room_id: str):
        self.active_user_rooms[str(user_id)] = str(room_id)

    async def broadcast_room(self, message: dict, room_id: str, exclude: WebSocket = None):
        rid = str(room_id)
        if rid in self.active_room_connections:
            for connection in self.active_room_connections[rid]:
                if connection != exclude:
                    try:
                        await connection.send_json(message)
                    except:
                        pass

    async def broadcast_chat_to_room(self, message: dict, room_id: str, exclude_user_id: str = None):
        # Broadcast to everyone currently viewing the room via their chat socket
        rid = str(room_id)
        exid = str(exclude_user_id) if exclude_user_id else None
        for uid, r_id in self.active_user_rooms.items():
            if r_id == rid and uid != exid:
                await self.send_to_user(message, uid)

    async def send_to_user(self, message: dict, user_id: str):
        uid = str(user_id)
        if uid in self.active_user_connections:
            try:
                await self.active_user_connections[uid].send_json(message)
            except:
                pass

manager = ConnectionManager()
