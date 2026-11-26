export type Analysis = {
  id: number; job_title: string; score: number;
  matched: string[]; missing: string[]; created: string; advice: string;
  breakdown?: { skill_coverage: number; text_similarity: number; confidence: string; skills_considered: number };
  evidence?: { matched: Record<string, string>; missing: Record<string, string> };
  disclaimer?: string;
};
export type Stats = { total: number; average: number; best: number };

export const session = {
  get token() { return localStorage.getItem("token"); },
  get email() { return localStorage.getItem("email"); },
  set(token: string, email: string) { localStorage.setItem("token", token); localStorage.setItem("email", email); },
  clear() { localStorage.removeItem("token"); localStorage.removeItem("email"); },
};

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`/api${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(session.token ? { Authorization: `Bearer ${session.token}` } : {}),
    },
  });
  if (res.status === 204) return undefined as T;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    if (res.status === 401 && session.token) { session.clear(); location.href = "/login"; }
    const d = data.detail;
    throw new Error(typeof d === "string" ? d : Array.isArray(d) ? d[0]?.msg?.replace("Value error, ", "") ?? "Check your input." : "Something went wrong.");
  }
  return data as T;
}
