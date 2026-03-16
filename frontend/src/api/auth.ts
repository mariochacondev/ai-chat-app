type JwtPayload = { exp?: number; [k: string]: any };

function decodeJwt(token: string): JwtPayload | null {
  try {
    const [, payload] = token.split(".");
    if (!payload) return null;
    const base64 = payload.replace(/-/g, "+").replace(/_/g, "/");
    const json = atob(base64);
    return JSON.parse(
      decodeURIComponent(
        Array.from(json)
          .map((c) => "%" + c.charCodeAt(0).toString(16).padStart(2, "0"))
          .join("")
      )
    );
  } catch {
    return null;
  }
}

export function getAccessToken() {
  return sessionStorage.getItem("access_token");
}
export function getRefreshToken() {
  return sessionStorage.getItem("refresh_token");
}
export function clearTokens() {
  sessionStorage.removeItem("access_token");
  sessionStorage.removeItem("refresh_token");
}

export function isAccessTokenValid(skewSeconds = 10): boolean {
  const token = getAccessToken();
  if (!token) return false;
  const payload = decodeJwt(token);
  if (!payload?.exp) return false;

  const now = Math.floor(Date.now() / 1000);
  return payload.exp > now + skewSeconds;
}

export function logout(): void {
  sessionStorage.removeItem("access_token");
  sessionStorage.removeItem("refresh_token");
}
