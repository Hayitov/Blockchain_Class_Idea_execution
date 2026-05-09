// Always send cookies — same-origin via the Vite proxy in dev.
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
