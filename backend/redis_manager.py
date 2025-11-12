import redis.asyncio as redis
import json
from typing import Optional
import os

class RedisManager:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis: Optional[redis.Redis] = None

    async def connect(self):
        self.redis = redis.from_url(self.redis_url, decode_responses=True)
        await self.redis.ping()
        print("Connected to Redis")
    
    async def disconnect(self):
        if self.redis:
            await self.redis.close()
            print("Disconnected from Redis")

    async def publish_message(self, room_id: str, message: dict):
        if self.redis:
            await self.redis.publish(F"room:{room_id}", json.dumps(message))

    async def subscribe_to_room(self, room_id: str, callback):
        if self.redis:
            pubsub = self.redis.pubsub()
            await pubsub.subscribe(F"room:{room_id}")
            print(F"Subscribed to room:{room_id}")

            async for message in pubsub.listen():
                if message['type'] == 'message':
                    data = json.loads(message['data'])
                    await callback(data)

    #Session storage
    async def store_user_session(self, user_id: str, session_data: dict):
        if self.redis:
            await self.redis.setex(F"user_session:{user_id}", 3600, json.dumps(session_data))

    async def get_user_session(self, user_id: str) -> Optional[dict]:
        if self.redis:
            data = await self.redis.get(F"user_session:{user_id}")
            return json.loads(data) if data else None
        
    #online user tracking
    async def add_online_user(self, room_id: str, user_id: str):
        if self.redis:
            await self.redis.sadd(F"room:{room_id}:online_users", user_id)
    
    async def remove_online_user(self, room_id: str, user_id: str):
        if self.redis:
            await self.redis.srem(F"room:{room_id}:online_users", user_id)

    async def get_online_users(self, room_id: str) -> list:
        if self.redis:
            return await self.redis.smembers(F"room:{room_id}:online_users")
        return []
    
    #Message caching (recent messages)
    async def cache_recent_message(self, room_id: str, message: dict):
        if self.redis:
            await self.redis.lpush(F"room:{room_id}:recent_messages", json.dumps(message))
            await self.redis.ltrim(F"room:{room_id}:recent_messages", 0, 49)  # Keep only the latest 50 messagesx