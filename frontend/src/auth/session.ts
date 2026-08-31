import { api, clearToken, getToken, type UserMe } from "../api";

const USER_KEY = "eaios_user";
const ORG_CONTEXT_KEY = "eaios_selected_org_id";

export function saveUser(user: UserMe): void {
  sessionStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getCachedUser(): UserMe | null {
  const raw = sessionStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as UserMe;
  } catch {
    return null;
  }
}

export function clearSession(): void {
  clearToken();
  sessionStorage.removeItem(USER_KEY);
  sessionStorage.removeItem(ORG_CONTEXT_KEY);
}

export function logout(): void {
  clearSession();
  window.location.href = "/login";
}

export async function validateSession(): Promise<UserMe> {
  const token = getToken();
  if (!token) {
    throw new Error("NO_TOKEN");
  }
  const user = await api<UserMe>("/api/auth/me");
  saveUser(user);
  return user;
}
