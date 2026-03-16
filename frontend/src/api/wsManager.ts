let ws: WebSocket | null = null;
let currentToken: string | null = null;

function getWsBaseUrl(): string {
  const httpBase = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";
  return httpBase.replace(/^http/, "ws") + "/chat/ws";
}

export function getOrCreateWs(token: string): WebSocket {
  if (ws && ws.readyState === WebSocket.OPEN && currentToken === token) return ws;
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
    if (currentToken === token) return ws;
    ws.close(1000, "token changed");
  }

  currentToken = token;
  const url = `${getWsBaseUrl()}?token=${encodeURIComponent(token)}`;
  ws = new WebSocket(url);
  return ws;
}

export function closeWs() {
  ws?.close(1000, "manual close");
  ws = null;
  currentToken = null;
}
