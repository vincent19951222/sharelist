export interface Member {
  memberId: string;
  name: string;
  joinedAt: number;
}

export type Priority = "high" | "medium" | "low";

export interface TodoItem {
  id: string;
  text: string;
  done: boolean;
  doneBy: string | null;
  priority?: Priority;  // Optional for backward compatibility
  createdAt: number;
  updatedAt: number;
}

export interface Room {
  roomId: string;
  roomName: string;
  createdAt: number;
  updatedAt: number;
  items: TodoItem[];
}

export interface RecentRoom {
  roomId: string;
  roomName: string;
  token?: string;
  role?: 'admin' | 'member' | 'guest';
  lastVisited: number;
}

export interface LocalUser {
  name: string;
  recentRooms: RecentRoom[]; 
}
