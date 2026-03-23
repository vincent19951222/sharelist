import { ProfileSummary, RoomAccessResponse, RoomSnapshot } from "@/types";

function getApiBase(): string {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }

  if (typeof window !== "undefined") {
    return `${window.location.protocol}//${window.location.hostname}:8000`;
  }

  return "http://localhost:8000";
}

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const detail =
      payload && typeof payload.detail === "string"
        ? payload.detail
        : "Request failed.";
    throw new Error(detail);
  }

  return response.json();
}

export async function accessRoom(roomId: string, name: string): Promise<RoomAccessResponse> {
  const response = await fetch(`${getApiBase()}/api/rooms/access`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ roomId, name }),
  });

  return parseJson<RoomAccessResponse>(response);
}

export async function getRoomSnapshot(
  roomId: string,
  name: string,
  signal?: AbortSignal
): Promise<RoomSnapshot> {
  const params = new URLSearchParams({ name });
  const response = await fetch(`${getApiBase()}/api/rooms/${roomId}/snapshot?${params.toString()}`, {
    cache: "no-store",
    signal,
  });

  return parseJson<RoomSnapshot>(response);
}

export async function getProfile(roomId: string, userId: string): Promise<ProfileSummary> {
  const response = await fetch(`${getApiBase()}/api/rooms/${roomId}/profiles/${userId}`, {
    cache: "no-store",
  });

  return parseJson<ProfileSummary>(response);
}
