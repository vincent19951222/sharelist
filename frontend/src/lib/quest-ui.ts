const WEEKDAY_LABELS: Record<string, string> = {
  Sun: "S",
  Mon: "M",
  Tue: "T",
  Wed: "W",
  Thu: "T",
  Fri: "F",
  Sat: "S",
};

export const DAY_ORDER = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"] as const;
export const REWARD_OPTIONS = [10, 20, 30, 40, 50];

export function weekdayPillLabel(day: string): string {
  return WEEKDAY_LABELS[day] ?? day.slice(0, 1);
}

export function formatHistoryTime(timestamp: number): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffDays = Math.floor((startOfDay(now).getTime() - startOfDay(date).getTime()) / 86400000);

  if (diffDays === 0) {
    return `Today · ${date.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}`;
  }

  if (diffDays === 1) {
    return `Yesterday · ${date.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}`;
  }

  return date.toLocaleString("zh-CN", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function startOfDay(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}
