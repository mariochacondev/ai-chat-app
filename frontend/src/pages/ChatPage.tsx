import {type FormEvent, useEffect, useRef, useState} from "react";
import {useNavigate} from "react-router-dom";
import {getOrCreateWs} from "../api/wsManager.ts";
import {getAccessToken, logout} from "../api/auth";
import {getCurrentUser} from "../api/me";
import client from "../api/client";


type Msg = { role: "user" | "assistant" | null; content: string | null };

type ConversationItem = {
    id: number;
    title: string;
    created_at?: string;
    updated_at?: string;
};


export default function ChatPage() {
    const navigate = useNavigate();
    const [prompt, setPrompt] = useState("");
    const [messages, setMessages] = useState<Msg[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isAdmin, setIsAdmin] = useState(false);

    // conversations
    const [conversations, setConversations] = useState<ConversationItem[]>([]);
    const [activeConversationId, setActiveConversationId] = useState<number | null>(null);
    const [loadingConversations, setLoadingConversations] = useState(false);

    const wsRef = useRef<WebSocket | null>(null);
    const assistantIndexRef = useRef<number | null>(null);
    const activeRequestIdRef = useRef<string | null>(null);
    const conversationIdRef = useRef<number | null>(null);

    getCurrentUser().then((data) => {
        setIsAdmin(data.is_admin)
    })

    function newRequestId() {
        return crypto.randomUUID();
    }

    async function refreshConversations(keepActive = true) {
        setLoadingConversations(true);
        try {
            const res = await client.get("/conversations/list");
            const list: ConversationItem[] = res.data?.conversations ?? [];
            setConversations(list);

            if (!keepActive) return;

            // if nothing selected yet, select the most recent
            if (conversationIdRef.current == null && list.length > 0) {
                const first = list[0];
                conversationIdRef.current = first.id;
                setActiveConversationId(first.id);
                await loadConversation(first.id);
            }
        } catch (err: any) {
            setError(err?.response?.data?.detail || err?.message || "Failed to load conversations");
        } finally {
            setLoadingConversations(false);
        }
    }

    async function loadConversation(conversationId: number) {
        setError(null);
        setLoading(false);
        assistantIndexRef.current = null;
        activeRequestIdRef.current = null;

        try {
            const res = await client.get(`/conversations/${conversationId}`);
            const msgs = (res.data?.messages ?? []) as Array<{ role: string; content: string }>;

            const mapped: Msg[] = msgs
                .filter((m) => m.role === "user" || m.role === "assistant")
                .map((m) => ({role: m.role as "user" | "assistant", content: m.content}));

            setMessages(mapped);
        } catch (err: any) {
            setError(err?.response?.data?.detail || err?.message || "Failed to load conversation");
        }
    }

    async function createNewConversation() {
        setError(null);
        try {
            const res = await client.post("/conversations/create");
            const convo = res.data as { id: number; title: string };

            // refresh list, select new convo
            await refreshConversations(false);

            conversationIdRef.current = convo.id;
            setActiveConversationId(convo.id);
            setMessages([]);
            await refreshConversations(true);
        } catch (err: any) {
            setError(err?.response?.data?.detail || err?.message || "Failed to create conversation");
        }
    }

    useEffect(() => {
        // 1) WS connect
        const token = getAccessToken();
        if (!token) return;

        const ws = getOrCreateWs(token);
        wsRef.current = ws;

        ws.onopen = () => console.log("WS open");
        ws.onerror = (e) => console.error("WS error", e);
        ws.onclose = (e) => console.warn("WS close", e.code, e.reason, e.wasClean);

        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);

            // ✅ ignore messages from older requests
            const activeRid = activeRequestIdRef.current;
            if (msg.request_id && activeRid && msg.request_id !== activeRid) return;

            if (msg.type === "start") {
                if (typeof msg.conversation_id === "number") {
                    conversationIdRef.current = msg.conversation_id;
                    setActiveConversationId(msg.conversation_id);
                    // refresh sidebar order (updated_at)
                    refreshConversations(true).catch(() => {
                    });
                }

                setMessages((m) => {
                    const next = [...m, {role: "assistant", content: ""} as Msg];
                    assistantIndexRef.current = next.length - 1;
                    return next;
                });
                return;
            }

            if (msg.type === "delta") {
                const delta: string = msg.content || "";
                const idx = assistantIndexRef.current;
                if (idx == null) return;

                setMessages((m) => {
                    if (!m[idx]) return m;
                    const next = [...m];
                    next[idx] = {...next[idx], content: next[idx].content + delta};
                    return next;
                });
                return;
            }

            if (msg.type === "done" || msg.type === "stopped") {
                setLoading(false);
                assistantIndexRef.current = null;
                activeRequestIdRef.current = null;
                // refresh sidebar (updated_at)
                refreshConversations(true).catch(() => {
                });
                return;
            }

            if (msg.type === "error") {
                setError(msg.message || "Stream error");
                setLoading(false);
                assistantIndexRef.current = null;
                activeRequestIdRef.current = null;
            }
        };

        // 2) load sidebar
        refreshConversations(true).catch(() => {
        });

        return () => {
            if (wsRef.current === ws) wsRef.current = null;
            ws.onmessage = null;
            ws.onerror = null;
            ws.onclose = null;
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    async function send(e: FormEvent) {
        e.preventDefault();
        setError(null);

        const requestId = newRequestId();
        activeRequestIdRef.current = requestId;

        const text = prompt.trim();
        if (!text || loading) return;

        setMessages((m) => [...m, {role: "user", content: text}]);
        setPrompt("");
        setLoading(true);

        const ws = wsRef.current;
        if (!ws) {
            setError("WebSocket not connected (refresh page).");
            setLoading(false);
            return;
        }

        const payload = {
            type: "prompt",
            request_id: requestId,
            prompt: text,
            conversation_id: conversationIdRef.current, // can be null => backend creates
        };

        if (ws.readyState === WebSocket.CONNECTING) {
            ws.addEventListener("open", () => ws.send(JSON.stringify(payload)), {once: true});
            return;
        }

        if (ws.readyState !== WebSocket.OPEN) {
            setError("WebSocket closed. Refresh page.");
            setLoading(false);
            return;
        }


        ws.send(JSON.stringify(payload));
    }

    function stop() {
        const ws = wsRef.current;
        const rid = activeRequestIdRef.current;
        if (!ws || ws.readyState !== WebSocket.OPEN || !rid) return;

        ws.send(JSON.stringify({type: "stop", request_id: rid}));
        // UI will be finalized by "stopped" or "done"
    }

    function onLogout() {
        logout();
        navigate("/auth?mode=login", {replace: true});
    }

    function uploadDoc() {
        navigate("/docs", {replace: true});
    }
;

    function adminPage() {
        if (isAdmin){
            navigate("/admin/users", {replace: true})
        }

    }

    async function onSelectConversation(id: number) {
        if (loading) return; // keep it simple: don’t switch mid-stream
        conversationIdRef.current = id;
        setActiveConversationId(id);
        await loadConversation(id);
    }

    return (
        <div style={{display: "flex", height: "100vh"}}>
            {/* Sidebar */}
            <div style={{width: 280, borderRight: "1px solid #eee", padding: 12, overflowY: "auto"}}>
                <div style={{display: "flex", gap: 8, alignItems: "center", marginBottom: 10}}>
                    <strong style={{flex: 1}}>Conversations</strong>
                    <button onClick={createNewConversation} disabled={loading}>
                        New
                    </button>
                </div>

                {loadingConversations && <div style={{color: "#666"}}>Loading…</div>}

                {!loadingConversations && conversations.length === 0 && (
                    <div style={{color: "#666"}}>No conversations yet.</div>
                )}

                <div style={{display: "flex", flexDirection: "column", gap: 6}}>
                    {conversations.map((c) => {
                        const active = c.id === activeConversationId;
                        return (
                            <button
                                key={c.id}
                                onClick={() => onSelectConversation(c.id)}
                                disabled={loading}
                                style={{
                                    textAlign: "left",
                                    padding: "10px 10px",
                                    borderRadius: 10,
                                    border: "1px solid #ddd",
                                    background: active ? "#f5f5f5" : "white",
                                    cursor: loading ? "not-allowed" : "pointer",
                                }}
                            >
                                <div style={{
                                    fontWeight: 600,
                                    fontSize: 14,
                                    overflow: "hidden",
                                    textOverflow: "ellipsis"
                                }}>
                                    {c.title || `Conversation ${c.id}`}
                                </div>
                                {c.updated_at && <div style={{fontSize: 12, color: "#666"}}>{c.updated_at}</div>}
                            </button>
                        );
                    })}
                </div>

                <div style={{marginTop: 12, display: "flex", gap: 8}}>
                    <button onClick={uploadDoc} style={{flex: 1}}>
                        Upload
                    </button>
                    <button onClick={onLogout} style={{flex: 1}}>
                        Logout
                    </button>
                    <button onClick={adminPage} style={{flex: 1}}>
                        Admin
                    </button>
                </div>
            </div>

            {/* Main chat */}
            <div style={{flex: 1, maxWidth: 900, margin: "0 auto", padding: 16, width: "100%"}}>
                <div style={{display: "flex", justifyContent: "space-between", alignItems: "center"}}>
                    <h2 style={{margin: 0}}>Chat</h2>
                    <div style={{color: "#666", fontSize: 12}}>
                        {activeConversationId ? `Conversation #${activeConversationId}` : "No conversation selected"}
                    </div>
                </div>

                <div style={{marginTop: 12, padding: 12, border: "1px solid #ddd", borderRadius: 10, minHeight: 360}}>
                    {messages.length === 0 && <div style={{color: "#666"}}>Say something…</div>}
                    {messages.map((m, idx) => (
                        <div key={idx} style={{margin: "10px 0"}}>
                            <div style={{fontSize: 12, color: "#666"}}>{m.role}</div>
                            <div style={{whiteSpace: "pre-wrap"}}>{m.content}</div>
                        </div>
                    ))}
                    {loading && <div style={{color: "#666"}}>Thinking…</div>}
                </div>

                {error && <div style={{marginTop: 10, color: "#b91c1c"}}>{error}</div>}

                <form onSubmit={send} style={{display: "flex", gap: 10, marginTop: 12}}>
                    <input
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                        placeholder="Type a message…"
                        style={{flex: 1, height: 44, borderRadius: 10, border: "1px solid #ddd", padding: "0 12px"}}
                    />
                    <button type="button" onClick={stop} disabled={!loading} style={{height: 44}}>
                        Stop
                    </button>
                    <button type="submit" disabled={loading} style={{height: 44}}>
                        Send
                    </button>
                </form>
            </div>
        </div>
    );
}
