import { nanoid } from 'nanoid';
import { Room, TodoItem, LocalUser } from '@/types';

const STORAGE_PREFIX = 'room-todo:';
const USER_KEY = 'room-todo:user';

// User Management
export function getLocalUser(): LocalUser {
  if (typeof window === 'undefined') return { name: '', recentRooms: [] };
  const data = localStorage.getItem(USER_KEY);
  if (!data) return { name: '', recentRooms: [] };
  
  try {
      const parsed = JSON.parse(data);
      // Migration Check: If recentRooms contains strings (old format), reset it
      if (Array.isArray(parsed.recentRooms) && parsed.recentRooms.length > 0) {
          if (typeof parsed.recentRooms[0] === 'string') {
              parsed.recentRooms = []; 
          }
      }
      return parsed;
  } catch (e) {
      return { name: '', recentRooms: [] };
  }
}

export function saveLocalUser(user: LocalUser) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function updateLocalUserName(name: string) {
  const user = getLocalUser();
  user.name = name;
  saveLocalUser(user);
}

export function addRecentRoom(roomId: string, roomName: string, token?: string, role?: 'admin' | 'member' | 'guest') {
  const user = getLocalUser();
  const now = Date.now();
  
  // Remove existing entry for this room to avoid duplicates
  const others = user.recentRooms.filter(r => r.roomId !== roomId);
  
  const newEntry = {
      roomId,
      roomName,
      token,
      role,
      lastVisited: now
  };
  
  // Add to top, keep max 10
  user.recentRooms = [newEntry, ...others].slice(0, 10);
  saveLocalUser(user);
}

// Room Management
function getRoomKey(roomId: string) {
  return `${STORAGE_PREFIX}room:${roomId}`;
}

export function getRoom(roomId: string): Room | null {
  if (typeof window === 'undefined') return null;
  const data = localStorage.getItem(getRoomKey(roomId));
  return data ? JSON.parse(data) : null;
}

export function saveRoom(room: Room) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(getRoomKey(room.roomId), JSON.stringify(room));
}

export function createRoom(roomName: string): Room {
  const room: Room = {
    roomId: nanoid(6), // Short ID for easier sharing
    roomName: roomName || 'New Room',
    createdAt: Date.now(),
    updatedAt: Date.now(),
    items: [],
  };
  saveRoom(room);
  return room;
}

export function updateRoomItems(roomId: string, items: TodoItem[]) {
  const room = getRoom(roomId);
  if (room) {
    room.items = items;
    room.updatedAt = Date.now();
    saveRoom(room);
  }
}

// Todo Item Helpers
export function createTodoItem(text: string): TodoItem {
  return {
    id: nanoid(),
    text,
    done: false,
    doneBy: null,
    createdAt: Date.now(),
    updatedAt: Date.now(),
  };
}
