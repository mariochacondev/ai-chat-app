import client from "../api/client";
import { getRefreshToken, clearTokens } from "./auth";

export async function refreshAccessToken(): Promise<string | null> {
  const refresh = getRefreshToken();
  if (!refresh) return null;

  try {
    const res = await client.post("/auth/refresh", {
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