const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface RoomCreated {
  roomId: string;
  roomName: string;
  adminToken: string;
  joinToken: string;
}

export async function createRoomApi(roomName: string): Promise<RoomCreated> {
  const res = await fetch(`${API_BASE}/api/rooms`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ roomName }),
  });
  
  if (!res.ok) {
    throw new Error('Failed to create room');
  }
  
  return res.json();
}

export interface RotateInviteResponse {
  newJoinToken: string;
}

export async function rotateInviteToken(roomId: string, adminToken: string): Promise<RotateInviteResponse> {
  const res = await fetch(`${API_BASE}/api/rooms/${roomId}/rotate-token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ adminToken }),
  });

  if (!res.ok) {
    throw new Error('Failed to rotate invite token');
  }

  return res.json();
}
