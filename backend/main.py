from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Chat WebSocket Microservice", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data Models
class User:
    def __init__(self, username: str, client_id: str, room_id: str):
        self.username = username
        self.client_id = client_id
        self.room_id = room_id
        self.joined_at = datetime.now()

class Room:
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.messages: List[dict] = []
        self.created_at = datetime.now()
        self.max_messages = 100  # Keep last 100 messages

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.rooms: Dict[str, Room] = {}
        self.users: Dict[str, User] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")
        
    async def disconnect(self, client_id: str):
        user = self.users.get(client_id)
        if user:
            await self._leave_room(client_id, user.room_id)
            del self.users[client_id]
            
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            
        logger.info(f"Client {client_id} disconnected")
    
    async def join_room(self, client_id: str, room_id: str, username: str):
        # Create room if it doesn't exist
        if room_id not in self.rooms:
            self.rooms[room_id] = Room(room_id)
            logger.info(f"Created new room: {room_id}")
        
        # Leave previous room if any
        old_user = self.users.get(client_id)
        if old_user and old_user.room_id != room_id:
            await self._leave_room(client_id, old_user.room_id)
        
        # Join new room
        self.users[client_id] = User(username, client_id, room_id)
        
        # Send room history to the new user
        room = self.rooms[room_id]
        await self._send_to_client(client_id, {
            "event": "room_history",
            "data": {
                "messages": room.messages[-50:],  # Last 50 messages
                "room_id": room_id
            }
        })
        
        # Notify room about new user
        user_list = await self._get_room_users(room_id)
        await self._broadcast_to_room(room_id, {
            "event": "user_joined",
            "data": {
                "username": username,
                "message": f"{username} joined the room",
                "timestamp": datetime.now().isoformat(),
                "users": user_list,
                "room_id": room_id
            }
        })
        
        logger.info(f"User {username} joined room {room_id}")
    
    async def send_message(self, client_id: str, message_text: str):
        user = self.users.get(client_id)
        if not user:
            await self._send_to_client(client_id, {
                "event": "error",
                "data": {"message": "You must join a room first"}
            })
            return
        
        room_id = user.room_id
        room = self.rooms.get(room_id)
        
        if not room:
            await self._send_to_client(client_id, {
                "event": "error", 
                "data": {"message": "Room not found"}
            })
            return
        
        # Create message object
        message_data = {
            "id": str(uuid.uuid4()),
            "username": user.username,
            "message": message_text,
            "timestamp": datetime.now().isoformat(),
            "room_id": room_id
        }
        
        # Store message
        room.messages.append(message_data)
        # Keep only recent messages
        if len(room.messages) > room.max_messages:
            room.messages = room.messages[-room.max_messages:]
        
        # Broadcast to room
        await self._broadcast_to_room(room_id, {
            "event": "new_message",
            "data": message_data
        })
        
        logger.info(f"Message in {room_id}: {user.username}: {message_text}")
    
    async def _leave_room(self, client_id: str, room_id: str):
        user = self.users.get(client_id)
        if not user:
            return
            
        # Notify room about user leaving
        user_list = await self._get_room_users(room_id)
        user_list = [u for u in user_list if u != user.username]
        
        await self._broadcast_to_room(room_id, {
            "event": "user_left",
            "data": {
                "username": user.username,
                "message": f"{user.username} left the room",
                "timestamp": datetime.now().isoformat(),
                "users": user_list,
                "room_id": room_id
            }
        })
    
    async def _get_room_users(self, room_id: str) -> List[str]:
        users_in_room = []
        for user in self.users.values():
            if user.room_id == room_id:
                users_in_room.append(user.username)
        return list(set(users_in_room))  # Remove duplicates
    
    async def _broadcast_to_room(self, room_id: str, message: dict):
        disconnected_clients = []
        
        for client_id, user in self.users.items():
            if user.room_id == room_id and client_id in self.active_connections:
                try:
                    await self.active_connections[client_id].send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to client {client_id}: {e}")
                    disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    async def _send_to_client(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending to client {client_id}: {e}")
                self.disconnect(client_id)

# Global connection manager
manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive and parse JSON message
            data = await websocket.receive_json()
            event_type = data.get("event")
            
            if event_type == "join_room":
                room_id = data.get("room_id", "general")
                username = data.get("username", f"User_{client_id}")
                await manager.join_room(client_id, room_id, username)
                
            elif event_type == "send_message":
                message = data.get("message", "").strip()
                if message:  # Only send non-empty messages
                    await manager.send_message(client_id, message)
                    
            elif event_type == "ping":
                await websocket.send_json({"event": "pong"})
                
            else:
                await websocket.send_json({
                    "event": "error", 
                    "data": {"message": f"Unknown event: {event_type}"}
                })
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        manager.disconnect(client_id)

# HTTP Routes for monitoring
@app.get("/")
async def root():
    return {
        "service": "Chat WebSocket Microservice",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "active_connections": len(manager.active_connections),
        "active_rooms": len(manager.rooms),
        "total_users": len(manager.users)
    }

@app.get("/stats")
async def get_stats():
    room_stats = {}
    for room_id, room in manager.rooms.items():
        room_stats[room_id] = {
            "message_count": len(room.messages),
            "user_count": len([u for u in manager.users.values() if u.room_id == room_id])
        }
    
    return {
        "active_connections": len(manager.active_connections),
        "active_rooms": len(manager.rooms),
        "total_users": len(manager.users),
        "room_stats": room_stats
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")