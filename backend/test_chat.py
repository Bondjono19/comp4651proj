import asyncio
import websockets
import json
import sys

class ChatClient:
    def __init__(self, client_id, username, room_id="general"):
        self.client_id = client_id
        self.username = username
        self.room_id = room_id
        self.uri = f"ws://localhost:8000/ws/{client_id}"
        self.websocket = None
    
    async def connect(self):
        self.websocket = await websockets.connect(self.uri)
        print(f"🚀 Connecting as {self.username} to room '{self.room_id}'...")
        
        # Join room immediately after connection
        join_message = {
            "event": "join_room",
            "room_id": self.room_id,
            "username": self.username
        }
        await self.websocket.send(json.dumps(join_message))
        print(f"✅ Joined room '{self.room_id}' as {self.username}")
        print("\nCommands:")
        print("  /room <room_name> - Switch to another room")
        print("  /users - List users in current room")
        print("  /quit - Exit the chat")
        print("  Or just type messages to send!\n")
    
    async def listen(self):
        try:
            async for message in self.websocket:
                data = json.loads(message)
                event = data.get("event")
                
                if event == "new_message":
                    msg_data = data.get("data", {})
                    print(f"💬 {msg_data.get('username')}: {msg_data.get('message')}")
                    
                elif event == "user_joined":
                    join_data = data.get("data", {})
                    print(f"👋 {join_data.get('message')}")
                    if join_data.get('users'):
                        print(f"   👥 Users in room: {', '.join(join_data['users'])}")
                        
                elif event == "user_left":
                    leave_data = data.get("data", {})
                    print(f"👋 {leave_data.get('message')}")
                    
                elif event == "room_history":
                    history_data = data.get("data", {})
                    messages = history_data.get("messages", [])
                    if messages:
                        print(f"\n📜 Last {len(messages)} messages in this room:")
                        for msg in messages:
                            print(f"   {msg.get('username')}: {msg.get('message')}")
                    print("")  # Empty line after history
                    
                elif event == "error":
                    error_data = data.get("data", {})
                    print(f"❌ Error: {error_data.get('message')}")
                    
        except Exception as e:
            print(f"📡 Connection lost: {e}")
    
    async def send_message(self, text: str):
        if text.startswith('/'):
            if text.startswith('/room '):
                new_room = text.split(' ', 1)[1]
                self.room_id = new_room
                join_message = {
                    "event": "join_room",
                    "room_id": self.room_id,
                    "username": self.username
                }
                await self.websocket.send(json.dumps(join_message))
                print(f"🔄 Switching to room '{new_room}'...")
                
            elif text == '/users':
                print("💡 Use '/room <name>' to see users in that room")
                
            elif text == '/quit':
                return False
                
            else:
                print("❌ Unknown command")
        else:
            # Regular message
            message_data = {
                "event": "send_message",
                "message": text
            }
            await self.websocket.send(json.dumps(message_data))
            print(f"📤 You: {text}")
        
        return True
    
    async def run(self):
        await self.connect()
        
        # Start listening in background
        listen_task = asyncio.create_task(self.listen())
        
        try:
            while True:
                try:
                    text = await asyncio.get_event_loop().run_in_executor(
                        None, input, ""
                    )
                    
                    if not await self.send_message(text.strip()):
                        break
                        
                except (KeyboardInterrupt, EOFError):
                    print("\n👋 Goodbye!")
                    break
                    
        finally:
            listen_task.cancel()
            await self.websocket.close()

async def main():
    if len(sys.argv) > 1:
        client_id = sys.argv[1]
    else:
        client_id = input("Enter client ID: ").strip() or f"client_{int(asyncio.get_event_loop().time())}"
    
    if len(sys.argv) > 2:
        username = sys.argv[2]
    else:
        username = input("Enter your username: ").strip() or f"User_{client_id}"
    
    if len(sys.argv) > 3:
        room_id = sys.argv[3]
    else:
        room_id = input("Enter room ID (default: general): ").strip() or "general"
    
    client = ChatClient(client_id, username, room_id)
    await client.run()

if __name__ == "__main__":
    asyncio.run(main())