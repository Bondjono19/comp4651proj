import redis.asyncio as redis
import json
from typing import Optional
import os

class RedisManager:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis: Optional[redis.Redis] = None
        self.is_connected = False

    async def connect(self):
        self.redis = redis.from_url(self.redis_url, decode_responses=True)
        await self.redis.ping()
        self.is_connected = True
        print("✅ Connected to Redis")
    
    async def disconnect(self):
        if self.redis:
            await self.redis.close()
            self.is_connected = False
            print("🔌 Disconnected from Redis")

    async def publish_message(self, room_id: str, message: dict):
        if self.redis and self.is_connected:
            await self.redis.publish(f"room:{room_id}", json.dumps(message))
            print(f"📤 Published message to room:{room_id}")
        else:
            print(f"⚠️  Redis not connected - message not published to {room_id}")

    async def subscribe_to_room(self, room_id: str, callback):
        if self.redis and self.is_connected:
            try:
                pubsub = self.redis.pubsub()
                await pubsub.subscribe(f"room:{room_id}")
                print(f"✅ Subscribed to Redis channel: room:{room_id}")
                
                async for message in pubsub.listen():
                    if message['type'] == 'message':
                        print(f"🔍 Redis received message on {room_id}: {message['data']}")
                        try:
                            data = json.loads(message['data'])
                            await callback(data)
                        except json.JSONDecodeError as e:
                            print(f"❌ Error parsing Redis message: {e}")
            except Exception as e:
                print(f"❌ Redis subscription error for {room_id}: {e}")
        else:
            print(f"❌ Cannot subscribe to {room_id} - Redis not connected")

    # Session storage
    async def store_user_session(self, user_id: str, session_data: dict):
        if self.redis and self.is_connected:
            await self.redis.setex(f"user_session:{user_id}", 3600, json.dumps(session_data))

    async def get_user_session(self, user_id: str) -> Optional[dict]:
        if self.redis and self.is_connected:
            data = await self.redis.get(f"user_session:{user_id}")
            return json.loads(data) if data else None
        return None
        
    # Online user tracking
    async def add_online_user(self, room_id: str, user_id: str):
        if self.redis and self.is_connected:
            await self.redis.sadd(f"room:{room_id}:online_users", user_id)

    async def remove_online_user(self, room_id: str, user_id: str):
        if self.redis and self.is_connected:
            await self.redis.srem(f"room:{room_id}:online_users", user_id)

    async def get_online_users(self, room_id: str) -> list:
        if self.redis and self.is_connected:
            return await self.redis.smembers(f"room:{room_id}:online_users")
        return []
    
    # Message caching - recent messages
    async def cache_recent_message(self, room_id: str, message: dict):
        if self.redis and self.is_connected:
            await self.redis.lpush(f"room:{room_id}:recent_messages", json.dumps(message))
            await self.redis.ltrim(f"room:{room_id}:recent_messages", 0, 49)

    async def get_recent_messages(self, room_id: str) -> list:
        if self.redis and self.is_connected:
            messages = await self.redis.lrange(f"room:{room_id}:recent_messages", 0, -1)
            return [json.loads(msg) for msg in messages]
        return []
