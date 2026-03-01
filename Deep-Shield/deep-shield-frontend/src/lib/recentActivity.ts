const KEY = "deepshield_recent";
const MAX = 10;

export interface RecentItem {
  path: string;
  label: string;
  ts: number;
}

export function getRecent(): RecentItem[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return [];
    const arr = JSON.parse(raw) as RecentItem[];
    return Array.isArray(arr) ? arr.slice(0, MAX) : [];
  } catch {
    return [];
  }
}

export function addRecent(item: Omit<RecentItem, "ts">): void {
  if (typeof window === "undefined") return;
  try {
    const prev = getRecent();
    const next = [
      { ...item, ts: Date.now() },
      ...prev.filter((x) => x.path !== item.path),
    ].slice(0, MAX);
    localStorage.setItem(KEY, JSON.stringify(next));
  } catch {
    // ignore
  }
}
