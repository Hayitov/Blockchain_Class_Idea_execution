async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const r = await fetch(path, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(init.headers ?? {}) },
    ...init,
  });
  if (!r.ok) {
    let detail: string;
    try {
      detail = (await r.json()).detail ?? r.statusText;
    } catch {
      detail = r.statusText;
    }
    throw new Error(`${r.status} ${detail}`);
  }
  return r.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
};

export type Me = {
  address: string;
  student: {
    id: number;
    eth_address: string;
    name: string;
    student_id: string | null;
    github: string | null;
  } | null;
};

export type Nonce = { nonce: string; issued_at: string };

export type Assignment = {
  id: number;
  code: string;
  title: string;
  weight: number;
};

export type GraderRun = {
  id: number;
  submission_id: number;
  status: "ok" | "error";
  score: number | null;
  details_json: Record<string, unknown>;
  created_at: string;
};

export type Submission = {
  id: number;
  student_id: number;
  assignment_id: number;
  assignment_code: string;
  created_at: string;
  runs: GraderRun[];
};
