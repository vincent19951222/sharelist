import pytest
import httpx
import asyncio
import websockets
import json
import uuid

# Configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

# Helpers
def generate_client_event_id():
    return str(uuid.uuid4())

@pytest.mark.asyncio
async def test_create_room():
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/api/rooms", json={"roomName": "Test Room"})
        assert response.status_code == 200
        data = response.json()
        assert "roomId" in data
        assert "adminToken" in data
        assert "joinToken" in data
        return data

@pytest.mark.asyncio
async def test_websocket_flow():
    # 1. Create Room
    room_data = await test_create_room()
    room_id = room_data["roomId"]
    admin_token = room_data["adminToken"]
    join_token = room_data["joinToken"]

    # 2. Admin Connects
    admin_uri = f"{WS_URL}/ws/{room_id}/AdminUser?token={admin_token}"
    async with websockets.connect(admin_uri) as admin_ws:
        # Receive Snapshot
        msg = await admin_ws.recv()
        snapshot = json.loads(msg)
        assert snapshot["type"] == "snapshot"
        assert snapshot["role"] == "admin"
        
        # 3. Member Connects
        member_uri = f"{WS_URL}/ws/{room_id}/MemberUser?token={join_token}"
        async with websockets.connect(member_uri) as member_ws:
            # Receive Snapshot
            msg = await member_ws.recv()
            snapshot = json.loads(msg)
            assert snapshot["type"] == "snapshot"
            assert snapshot["role"] == "member"

            # 4. Admin Adds Item (Sanitization Test)
            item_text = "Hello <b>World</b>"
            await admin_ws.send(json.dumps({
                "type": "item_add",
                "payload": {
                    "text": item_text,
                    "clientEventId": generate_client_event_id()
                }
            }))

            # 5. Member Receives Update
            # Member might receive ping or other messages, so loop until snapshot
            found_update = False
            for _ in range(5):
                msg = await member_ws.recv()
                data = json.loads(msg)
                if data["type"] == "snapshot":
                    items = data["payload"]["items"]
                    if items:
                        # Verify Sanitization (should be plain text)
                        assert items[0]["text"] == "Hello World" 
                        found_update = True
                        break
            assert found_update

@pytest.mark.asyncio
async def test_auth_failure():
    # Create Room
    room_data = await test_create_room()
    room_id = room_data["roomId"]
    
    # Try with Bad Token
    bad_uri = f"{WS_URL}/ws/{room_id}/Hacker?token=invalid_token"
    
    with pytest.raises(websockets.exceptions.ConnectionClosed) as excinfo:
        async with websockets.connect(bad_uri):
            pass
    
    # Verify Close Code (4001: Unauthorized)
    assert excinfo.value.code == 4001

@pytest.mark.asyncio
async def test_token_rotation():
    # 1. Create Room
    room_data = await test_create_room()
    room_id = room_data["roomId"]
    admin_token = room_data["adminToken"]
    old_join_token = room_data["joinToken"]
    
    # 2. Connect Member
    member_uri = f"{WS_URL}/ws/{room_id}/OldMember?token={old_join_token}"
    async with websockets.connect(member_uri) as member_ws:
        await member_ws.recv() # Snapshot
        
        # 3. Admin Rotates Token via REST
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BASE_URL}/api/rooms/{room_id}/rotate-token",
                json={"adminToken": admin_token}
            )
            assert resp.status_code == 200
            new_join_token = resp.json()["newJoinToken"]
            assert new_join_token != old_join_token
            
        # 4. Member receives notification
        msg = await member_ws.recv()
        data = json.loads(msg)
        assert data["type"] == "token_rotated"
        assert data["payload"]["newJoinToken"] == new_join_token
