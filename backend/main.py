import asyncio
import os  
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from mongodb_manager import mongodb_manager
from redis_manager import RedisManager
import uuid
from datetime import datetime
from typing import Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Chat WebSocket Microservice")

POD_NAME = os.getenv("POD_NAME","unknown")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost",
        "http://frontend",
        "http://frontend:80",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOMS = ["general", "python", "devops", "random"]

# Initialize managers
redis_manager = RedisManager()

@app.on_event("startup")
async def startup_event():
    # Connect to MongoDB
    await mongodb_manager.connect()
    
    # Connect to Redis
    await redis_manager.connect()
    
    # Ensure default rooms exist
    await ensure_default_rooms()
    
    # Start Redis subscribers
    asyncio.create_task(start_redis_subscribers())
    
    logger.info("✅ All services connected and ready!")

async def ensure_default_rooms():
    """Ensure default rooms exist in MongoDB"""
    default_rooms = [
        {"_id": "general", "name": "General Chat", "description": "Main discussion room"},
        {"_id": "python", "name": "Python Programming", "description": "Python-related discussions"},
        {"_id": "devops", "name": "DevOps & Cloud", "description": "Cloud infrastructure and DevOps"},
        {"_id": "random", "name": "Random Discussions", "description": "Off-topic conversations"}
    ]
    
    for room in default_rooms:
        existing_room = await mongodb_manager.get_room(room["_id"])
        if not existing_room:
            await mongodb_manager.db.rooms.insert_one(room)
            logger.info(f"✅ Created room: {room['name']}")

async def start_redis_subscribers():
    rooms = ["general", "python", "devops", "random"]
    for room in rooms:
        asyncio.create_task(
            redis_manager.subscribe_to_room(room, handle_redis_message)
        )
        logger.info(f"🔄 Started Redis subscriber for: {room}")

async def handle_redis_message(message: dict):
    room_id = message.get("room_id")
    if room_id:
        await manager._broadcast_to_room(room_id, message)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_rooms: Dict[str, str] = {}
        self.usernames: Dict[str, str] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected on Pod: {POD_NAME}")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            room_id = self.user_rooms.get(client_id)
            username = self.usernames.get(client_id)
            
            if room_id and username:
                # Notify others via Redis
                leave_message = {
                    "id": str(uuid.uuid4()),
                    "username": "System",
                    "content": f"{username} left the chat",
                    "timestamp": int(datetime.now().timestamp() * 1000),
                    "room_id": room_id
                }
                asyncio.create_task(redis_manager.publish_message(room_id, leave_message))
                
                # Remove from online users in Redis
                asyncio.create_task(redis_manager.remove_online_user(room_id, username))
            
            # Clean up
            if client_id in self.user_rooms:
                del self.user_rooms[client_id]
            if client_id in self.usernames:
                del self.usernames[client_id]
            if client_id in self.active_connections:
                del self.active_connections[client_id]
            
            logger.info(f"Client {client_id} disconnected")
    
    async def handle_join_room(self, client_id: str, data: dict):
        room_id = data.get("roomId", "general")
        username = data.get("username", f"User_{client_id}")
        
        # Get or create user in MongoDB
        user_id = await mongodb_manager.get_or_create_user(username)
        
        # Store user info
        self.user_rooms[client_id] = room_id
        self.usernames[client_id] = username
        
        # Update online users in Redis
        await redis_manager.add_online_user(room_id, username)
        
        # Get recent messages from Redis cache first
        recent_messages = await redis_manager.get_recent_messages(room_id)
        
        # If Redis cache is empty, fallback to MongoDB
        if not recent_messages:
            recent_messages = await mongodb_manager.get_recent_messages(room_id, 50)
            # Cache the messages in Redis for future requests
            for message in recent_messages:
                await redis_manager.cache_recent_message(room_id, message)
        
        # Send welcome and recent messages
        if client_id in self.active_connections:
            welcome_message = {
                "id": str(uuid.uuid4()),
                "username": "System",
                "content": f"Welcome to room '{room_id}'",
                "timestamp": int(datetime.now().timestamp() * 1000),
                "room_id": room_id
            }
            await self.active_connections[client_id].send_json(welcome_message)
            
            # Send recent messages
            for message in recent_messages:
                await self.active_connections[client_id].send_json(message)
        
        # Get online users from Redis
        online_users = await redis_manager.get_online_users(room_id)
        
        # Notify others via Redis
        join_message = {
            "id": str(uuid.uuid4()),
            "username": "System",
            "content": f"{username} joined the chat",
            "timestamp": int(datetime.now().timestamp() * 1000),
            "room_id": room_id,
            "online_users": list(online_users)
        }
        await redis_manager.publish_message(room_id, join_message)
        
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
        
        message_data = {
            "id": str(uuid.uuid4()),
            "username": username,
            "content": data.get("content", ""),
            "timestamp": int(datetime.now().timestamp() * 1000),
            "room_id": room_id
        }
        
        # Cache in Redis first
        await redis_manager.cache_recent_message(room_id, message_data)
        
        # Publish to Redis pub/sub for real-time delivery
        await redis_manager.publish_message(room_id, message_data)
        
        # Store in MongoDB asynchronously
        asyncio.create_task(mongodb_manager.save_message(message_data))
        
        logger.info(f"Message in {room_id}: {username}: {message_data['content']}")
    
    async def _broadcast_to_room(self, room_id: str, message: dict, exclude_client: str = None):
        disconnected_clients = []
        
        for client_id, websocket in self.active_connections.items():
            if (self.user_rooms.get(client_id) == room_id and 
                client_id != exclude_client):
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to client {client_id}: {e}")
                    disconnected_clients.append(client_id)
        
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    async def _send_error(self, client_id: str, message: str):
        error_msg = {
            "id": str(uuid.uuid4()),
            "username": "System",
            "content": message,
            "timestamp": int(datetime.now().timestamp() * 1000)
        }
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(error_msg)

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
                await manager._send_error(client_id, "Unknown message format")
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        manager.disconnect(client_id)

# HTTP Routes
@app.get("/")
async def root():
    return {"service": "Chat WebSocket", "status": "running", "database": "MongoDB"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "active_connections": len(manager.active_connections),
        "database": "MongoDB"
    }

@app.get("/metrics")
async def get_metrics():
    rooms = ["general", "python", "devops", "random"]
    room_metrics = {}
    
    for room in rooms:
        stats = await mongodb_manager.get_room_stats(room)
        room_metrics[room] = stats
    
    return {
        "server_id": os.getenv("HOSTNAME", "backend-1"),
        "active_connections": len(manager.active_connections),
        "room_metrics": room_metrics,
        "timestamp": int(datetime.now().timestamp() * 1000)
    }

@app.get("/rooms")
async def list_rooms():
    rooms = await mongodb_manager.get_all_rooms()
    return {
        "rooms": rooms,
        "database": "MongoDB"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")