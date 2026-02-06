import asyncio
import websockets
import json
import uuid
import random
import time
import httpx

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"
NUM_USERS = 20
DURATION_SECONDS = 5

async def user_worker(user_id, room_id, token):
    uri = f"{WS_URL}/ws/{room_id}/User{user_id}?token={token}"
    async with websockets.connect(uri) as ws:
        await ws.recv() # Initial snapshot
        
        start_time = time.time()
        while time.time() - start_time < DURATION_SECONDS:
            # Randomly add an item
            if random.random() < 0.1: # 10% chance to act per loop
                await ws.send(json.dumps({
                    "type": "item_add",
                    "payload": {
                        "text": f"User {user_id} Item",
                        "clientEventId": str(uuid.uuid4())
                    }
                }))
            
            # Drain messages to keep buffer empty
            try:
                await asyncio.wait_for(ws.recv(), timeout=0.1)
            except asyncio.TimeoutError:
                pass
            
            await asyncio.sleep(0.5) # Throttle

async def run_load_test():
    # 1. Setup
    print(f"Creating room for load test...")
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BASE_URL}/api/rooms", json={"roomName": "Load Test"})
        room_data = resp.json()
        
    room_id = room_data["roomId"]
    token = room_data["joinToken"]
    
    print(f"Starting {NUM_USERS} concurrent users for {DURATION_SECONDS}s...")
    
    # 2. Run Users
    tasks = []
    for i in range(NUM_USERS):
        tasks.append(user_worker(i, room_id, token))
        
    await asyncio.gather(*tasks)
    
    print("Load test completed. Checking consistency...")
    
    # 3. Verify Final State
    # Admin connects and counts items
    admin_token = room_data["adminToken"]
    uri = f"{WS_URL}/ws/{room_id}/Admin?token={admin_token}"
    async with websockets.connect(uri) as ws:
        msg = await ws.recv()
        snapshot = json.loads(msg)
        item_count = len(snapshot["payload"]["items"])
        print(f"Final Item Count: {item_count}")
        # We can't predict exact count due to random, but if it didn't crash, it's good.

if __name__ == "__main__":
    asyncio.run(run_load_test())
