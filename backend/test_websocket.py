import asyncio
import websockets
import json

async def test_websocket():
    client_id = "test_client_1"
    uri = f"ws://localhost:8000/ws/{client_id}"
    
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected successfully!")
            print("Type messages and press Enter. Type 'quit' to exit.")
            
            # Listen for incoming messages
            async def listen():
                try:
                    async for message in websocket:
                        print(f"\n📨 Received: {message}")
                except Exception as e:
                    print(f"Error receiving: {e}")
            
            # Send messages
            async def send():
                try:
                    while True:
                        message = await asyncio.get_event_loop().run_in_executor(
                            None, input, "> "
                        )
                        
                        if message.lower() == 'quit':
                            break
                            
                        await websocket.send(message)
                        print(f"📤 Sent: {message}")
                
                except Exception as e:
                    print(f"Error sending: {e}")
            
            # Run both tasks concurrently
            await asyncio.gather(listen(), send())
            
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())