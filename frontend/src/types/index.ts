export type MemberRole = "admin" | "member";
export type QuestSourceType = "manual" | "auto_quest";
export type Priority = "high" | "medium" | "low";

export interface RoomInfo {
  roomId: string;
  title: string;
  timezone: string;
}

export interface RoomUser {
  userId: string;
  name: string;
  displayName: string;
  avatarUrl: string;
}

export interface Member extends RoomUser {
  role: MemberRole;
  isOnline: boolean;
}

export interface TodoItem {
  id: string;
  title: string;
  done: boolean;
  rewardGp: number;
  sourceType: QuestSourceType;
  autoQuestId: string | null;
  scheduledDate: string | null;
  createdBy: string | null;
  completedBy: string | null;
  completedAt: number | null;
  createdAt: number;
  updatedAt: number;
}

export interface AutoQuest {
  id: string;
  title: string;
  rewardGp: number;
  repeatDays: string[];
  isEnabled: boolean;
  createdBy: string | null;
  createdAt: number;
  updatedAt: number;
}

export interface RoomSnapshot {
  room: RoomInfo;
  currentUser: Member;
  members: Member[];
  items: TodoItem[];
  autoQuests: AutoQuest[];
}

export interface LocalUser extends RoomUser {
  roomId: string;
  role: MemberRole;
}

export interface RoomAccessResponse {
  room: RoomInfo;
  user: Member;
}

export interface ProfileLedgerEntry {
  id: string;
  todoItemId: string;
  todoTitle: string;
  gpDelta: number;
  awardedAt: number;
}

export interface ProfileSummary extends RoomUser {
  rank: string;
  totalGp: number;
  thisWeekGp: number;
  thisWeekCount: number;
  thisMonthGp: number;
  thisMonthCount: number;
  history: ProfileLedgerEntry[];
}
