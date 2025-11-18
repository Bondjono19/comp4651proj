import motor.motor_asyncio
from datetime import datetime
import os
from typing import Optional, List

class MongoDBManager:
    def __init__(self):
        self.mongo_url = os.getenv("MONGO_URL", "mongodb://mongodb:27017/chatroom")
        self.client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self.db = None
    
    async def connect(self):
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(self.mongo_url)
            self.db = self.client.get_database()
            await self.db.command("ping")
            print("✅ Connected to MongoDB successfully!")
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            raise
    
    async def disconnect(self):
        if self.client:
            self.client.close()
    
    # User operations
    async def create_user(self, username: str) -> str:
        user_data = {
            "username": username,
            "created_at": datetime.now()
        }
        result = await self.db.users.insert_one(user_data)
        return str(result.inserted_id)
    
    async def get_or_create_user(self, username: str) -> str:
        """Get existing user or create new one"""
        user = await self.db.users.find_one({"username": username})
        if user:
            return str(user["_id"])
        else:
            return await self.create_user(username)
    
    async def get_user(self, username: str) -> Optional[dict]:
        user = await self.db.users.find_one({"username": username})
        if user:
            user["_id"] = str(user["_id"])
        return user
    
    # Message operations - stores timestamp as number (milliseconds)
    async def save_message(self, message_data: dict) -> str:
        message_to_store = message_data.copy()
        # Ensure timestamp is stored as a number for consistency
        if 'timestamp' not in message_to_store:
            message_to_store['timestamp'] = int(datetime.now().timestamp() * 1000)
        
        result = await self.db.messages.insert_one(message_to_store)
        message_id = str(result.inserted_id)
        print(f"✅ MongoDB stored message with ID: {message_id}")
        return message_id
    
    async def get_recent_messages(self, room_id: str, limit: int = 50) -> List[dict]:
        cursor = self.db.messages.find(
            {"room_id": room_id}
        ).sort("timestamp", -1).limit(limit)
        
        messages = []
        async for message in cursor:
            message["_id"] = str(message["_id"])
            messages.append(message)
        
        return list(reversed(messages))  # Return in chronological order
    
    async def get_room_messages_count(self, room_id: str) -> int:
        return await self.db.messages.count_documents({"room_id": room_id})
    
    # Room operations
    async def get_room(self, room_id: str) -> Optional[dict]:
        room = await self.db.rooms.find_one({"_id": room_id})
        if room:
            room["_id"] = str(room["_id"])
        return room
    
    async def get_all_rooms(self) -> List[dict]:
        cursor = self.db.rooms.find()
        rooms = []
        async for room in cursor:
            room["_id"] = str(room["_id"])
            rooms.append(room)
        return rooms
    
    # Statistics
    async def get_room_stats(self, room_id: str) -> dict:
        message_count = await self.get_room_messages_count(room_id)
        
        # Get unique users in this room (last 24 hours)
        one_day_ago = int((datetime.now().timestamp() - 86400) * 1000)
        pipeline = [
            {"$match": {"room_id": room_id, "timestamp": {"$gte": one_day_ago}}},
            {"$group": {"_id": "$username"}},
            {"$count": "unique_users"}
        ]
        
        unique_users_result = await self.db.messages.aggregate(pipeline).to_list(length=1)
        unique_users = unique_users_result[0]["unique_users"] if unique_users_result else 0
        
        return {
            "message_count": message_count,
            "active_users_today": unique_users
        }

# Global MongoDB manager instance
mongodb_manager = MongoDBManager()
