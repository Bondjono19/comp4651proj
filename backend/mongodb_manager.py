import motor.motor_asyncio
from datetime import datetime, UTC
import os
from typing import Optional, List
import json

class MongoDBManager:
    def __init__(self):
        self.mongo_url = os.getenv("MONGO_URL", "mongodb+srv://<username>:<password>@cluster0.mongodb.net/mydatabase?retryWrites=true&w=majority")
        self.client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None # type: ignore
        self.db = None
    
    async def connect(self):
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(self.mongo_url)
            self.db = self.client.get_database()  
            await self.db.command("ping")  # test connection
            print("✅ Connected to MongoDB Atlas successfully!")
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
            "created_at": datetime.now(UTC)
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
    
    # Message operations - now receives already serialized data
    async def save_message(self, message_data: dict) -> str:
        # Convert ISO timestamp string back to datetime for MongoDB storage
        message_to_store = message_data.copy()
        if 'timestamp' in message_to_store and isinstance(message_to_store['timestamp'], str):
            try:
                # Convert ISO string back to datetime for proper MongoDB storage
                message_to_store['timestamp'] = datetime.fromisoformat(message_to_store['timestamp'].replace('Z', '+00:00'))
            except Exception as e:
                print(f"⚠️ Could not parse timestamp, using current time: {e}")
                message_to_store['timestamp'] = datetime.now(UTC)
        
        result = await self.db.messages.insert_one(message_to_store)
        message_id = str(result.inserted_id)
        print(f"✅ DEBUG MongoDB stored message with ID: {message_id}")
        return message_id
    
    async def get_recent_messages(self, room_id: str, limit: int = 50) -> List[dict]:
        cursor = self.db.messages.find(
            {"room_id": room_id}
        ).sort("timestamp", -1).limit(limit)
        
        messages = []
        async for message in cursor:
            message["_id"] = str(message["_id"])
            # Convert datetime to ISO string for JSON serialization
            if 'timestamp' in message and isinstance(message['timestamp'], datetime):
                message['timestamp'] = message['timestamp'].isoformat()
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
        one_day_ago = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
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