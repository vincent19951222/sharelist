import { LocalUser, Member } from "@/types";

const USER_KEY = "sharelist:v1:user";

export function getLocalUser(): LocalUser | null {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = window.localStorage.getItem(USER_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as LocalUser;
  } catch {
    return null;
  }
}

export function saveLocalUser(roomId: string, user: Member): LocalUser {
  const nextUser: LocalUser = {
    roomId,
    userId: user.userId,
    name: user.name,
    displayName: user.displayName,
    avatarUrl: user.avatarUrl,
    role: user.role,
  };

  if (typeof window !== "undefined") {
    window.localStorage.setItem(USER_KEY, JSON.stringify(nextUser));
  }

  return nextUser;
}

export function clearLocalUser(): void {
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(USER_KEY);
  }
}
