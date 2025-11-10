import asyncio
import os  
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import uuid
from datetime import datetime
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Chat WebSocket Microservice")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOMS = ["general", "python", "devops", "random"]

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.rooms: Dict[str, List[dict]] = {}
        self.user_rooms: Dict[str, str] = {}
        self.usernames: Dict[str, str] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            room_id = self.user_rooms.get(client_id)
            username = self.usernames.get(client_id)
            
            if room_id and username:
                leave_message = {
                    "id": str(uuid.uuid4()),
                    "username": "System",
                    "content": f"{username} left the chat",
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }
                # FIX: Add await
                asyncio.create_task(self._broadcast_to_room(room_id, leave_message))
                
            # Clean up user data
            if client_id in self.user_rooms:
                del self.user_rooms[client_id]
            if client_id in self.usernames:
                del self.usernames[client_id]
            
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected")
    
    async def handle_join_room(self, client_id: str, data: dict):
        room_id = data.get("roomId", "general")
        username = data.get("username", f"User_{client_id}")
        
        self.user_rooms[client_id] = room_id
        self.usernames[client_id] = username
        
        if room_id not in self.rooms:
            self.rooms[room_id] = []
        
        # Send welcome and history
        if client_id in self.active_connections:
            welcome_message = {
                "id": str(uuid.uuid4()),
                "username": "System",
                "content": f"Welcome to room '{room_id}'",
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
            await self.active_connections[client_id].send_json(welcome_message)
            
            # Send room history
            for message in self.rooms[room_id][-50:]:
                await self.active_connections[client_id].send_json(message)
        
        # Notify others
        join_message = {
            "id": str(uuid.uuid4()),
            "username": "System",
            "content": f"{username} joined the chat",
            "timestamp": int(datetime.now().timestamp() * 1000)
        }
        await self._broadcast_to_room(room_id, join_message, exclude_client=client_id)
        
        logger.info(f"User {username} joined room {room_id}")
    
    async def handle_send_message(self, client_id: str, data: dict):
        room_id = self.user_rooms.get(client_id)
        username = self.usernames.get(client_id)
        
        if not room_id or not username:
            error_message = {
                "id": str(uuid.uuid4()),
                "username": "System",
                "content": "Please join a room first",
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
            if client_id in self.active_connections:
                await self.active_connections[client_id].send_json(error_message)
            return
        
        message = {
            "id": str(uuid.uuid4()),
            "username": username,
            "content": data.get("content", ""),
            "timestamp": int(datetime.now().timestamp() * 1000)
        }
        
        self.rooms[room_id].append(message)
        self.rooms[room_id] = self.rooms[room_id][-100:]
        
        await self._broadcast_to_room(room_id, message)
        logger.info(f"Message in {room_id}: {username}: {message['content']}")
    
    async def _broadcast_to_room(self, room_id: str, message: dict, exclude_client: str = None):
        disconnected_clients = []
        
        for client_id, websocket in self.active_connections.items():
            if (self.user_rooms.get(client_id) == room_id and 
                client_id != exclude_client):
                try:
                    # FIX: Add await
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to client {client_id}: {e}")
                    disconnected_clients.append(client_id)
        
        for client_id in disconnected_clients:
            self.disconnect(client_id)

    async def get_room_stats(self):
        # FIX: Use correct user counting logic
        return {
            room_id: {
                "user_count": len([cid for cid, room in self.user_rooms.items() if room == room_id]),
                "message_count": len(self.rooms.get(room_id, [])),
                "active": room_id in self.rooms
            }
            for room_id in ROOMS
        }

# Global connection manager
manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if "roomId" in data and "username" in data:
                await manager.handle_join_room(client_id, data)
            elif "content" in data:
                await manager.handle_send_message(client_id, data)
            else:
                error_msg = {
                    "id": str(uuid.uuid4()),
                    "username": "System", 
                    "content": "Unknown message format",
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }
                await websocket.send_json(error_msg)
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        manager.disconnect(client_id)

# HTTP Routes
@app.get("/")
async def root():
    return {"service": "Chat WebSocket", "status": "running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "active_connections": len(manager.active_connections),
        "active_rooms": len(manager.rooms)
    }

@app.get("/metrics")
async def get_metrics():
    return {
        "server_id": os.getenv("HOSTNAME", "backend-1"),
        "active_connections": len(manager.active_connections),
        "room_metrics": await manager.get_room_stats(),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/rooms")
async def list_rooms():
    return {
        "rooms": ROOMS,
        "description": {
            "general": "Main discussion room",
            "python": "Python programming chat", 
            "devops": "Cloud and containers discussion",
            "random": "Off-topic conversations"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")