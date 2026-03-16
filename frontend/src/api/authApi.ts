import { getRefreshToken, clearTokens } from "./auth";
import client from "../api/client";


const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";

export async function refreshAccessToken(): Promise<string | null> {
  const refresh = getRefreshToken();
  if (!refresh) return null;

  try {
    const res = await client.post(`${API_BASE}/auth/refresh`, {
      refresh_token: refresh,
    });

    const access = res.data?.access_token as string | undefined;
    if (!access) return null;

    sessionStorage.setItem("access_token", access);
    return access;
  } catch {
    clearTokens();
    return null;
  }
}
