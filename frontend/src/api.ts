const TOKEN_KEY = "eaios_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }
  const token = getToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const res = await fetch(path, { ...options, headers });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json() as Promise<T>;
}

export type UserMe = {
  id: string;
  username: string;
  role: string;
  organization_id: string;
  organization_name: string;
};

export type Organization = {
  id: string;
  name: string;
  created_at: string;
};

export type AuditLog = {
  id: string;
  action: string;
  detail: string | null;
  user_id: string | null;
  created_at: string;
};
