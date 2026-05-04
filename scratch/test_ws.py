import asyncio
import websockets
import json
API_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

async def test_room_broadcast():
    # Login as two different users (if possible, or just use IDs if we know them)
    # For simplicity, we'll try to connect with known user IDs from previous logs
    # user1: rudy (3050adbc-a3b4-48ff-90f8-11c2bc5262dd)
    # user2: deepti (7ab50294-a1d8-40d3-a8b4-cd20ed0f484f)
    
    u1_id = "3050adbc-a3b4-48ff-90f8-11c2bc5262dd"
    u2_id = "7ab50294-a1d8-40d3-a8b4-cd20ed0f484f"
    
    # We need a valid room_id.
    room_id = "b391a85a-1366-4f1c-bbd5-b5b14b0c2598" # from previous error log failing row

    print(f"Connecting User 2 ({u2_id})...")
    async with websockets.connect(f"{WS_URL}/ws/chat/{u2_id}") as ws2:
        print(f"Connecting User 1 ({u1_id})...")
        async with websockets.connect(f"{WS_URL}/ws/chat/{u1_id}") as ws1:
            
            # User 1 sends a room message
            msg = {
                "type": "chat",
                "room_id": room_id,
                "data": {
                    "id": "test-msg-id",
                    "sender_id": u1_id,
                    "content": "Hello Room!",
                    "timestamp": "2026-05-04T20:30:00Z"
                }
            }
            print("User 1 sending room message...")
            await ws1.send(json.dumps(msg))
            
            # User 2 should receive it
            try:
                print("User 2 waiting for message...")
                response = await asyncio.wait_for(ws2.recv(), timeout=5.0)
                received = json.loads(response)
                print("User 2 received:", received)
                if received["data"]["content"] == "Hello Room!":
                    print("SUCCESS: Room broadcast works!")
                else:
                    print("FAILURE: Received wrong message.")
            except asyncio.TimeoutError:
                print("FAILURE: User 2 timed out. No broadcast received.")

if __name__ == "__main__":
    asyncio.run(test_room_broadcast())
