import {useEffect, useState} from "react";
import client from "../api/client";
import {useNavigate} from "react-router-dom";

type DocRow = {
    doc_id: string;
    chunks: number;
    source?: string | null;
};

export default function DocsPage() {
    const navigate = useNavigate();
    const [file, setFile] = useState<File | null>(null);
    const [docId, setDocId] = useState("");
    const [status, setStatus] = useState<string | null>(null);
    const [busy, setBusy] = useState(false);

    const [docs, setDocs] = useState<DocRow[]>([]);
    const [loadingList, setLoadingList] = useState(false);

    async function refreshList() {
        setLoadingList(true);
        try {
            const res = await client.get("/docs/list");
            setDocs(res.data?.docs || []);
        } catch (e: any) {
            setStatus(e?.response?.data?.detail || e?.message || "Failed to load docs list");
        } finally {
            setLoadingList(false);
        }
    }

    useEffect(() => {
        refreshList();
    }, []);


    async function upload() {
        setStatus(null);
        if (!file) {
            setStatus("Pick a file first.");
            return;
        }

        const form = new FormData();
        form.append("file", file);

        const params = new URLSearchParams();
        if (docId.trim()) params.set("doc_id", docId.trim());
        params.set("chunk_size", "800");
        params.set("chunk_overlap", "100");

        setBusy(true);
        try {
            const res = await client.post(`/docs/upload?${params.toString()}`, form);

            const data = await res.data;
            if (!res.data) throw new Error(data?.detail || "Upload failed");

            setStatus(`✅ Uploaded. Inserted chunks: ${data.inserted} (doc_id: ${data.doc_id})`);
            setFile(null);
            await refreshList();
        } catch (e: any) {
            setStatus(`❌ ${e.message || "Upload failed"}`);
        } finally {
            setBusy(false);
        }
    }

    async function del(doc_id: string) {
        const ok = confirm(`Delete
        "${doc_id}" from your vector store?`);
        if (!ok) return;

        setStatus(null);
        try {
            await client.delete(`/docs/${encodeURIComponent(doc_id)}`);
            setStatus(`✅ Deleted ${doc_id}`);
            await refreshList();
        } catch (e: any) {
            setStatus(`❌ ${e?.response?.data?.detail || e?.message || "Delete failed"}`);
        }
    }

    function chatPage() {
        navigate("/chat", {replace: true})
    }

    return (
        <div style={{maxWidth: 900, margin: "0 auto", padding: 16}}>
            <h2 style={{marginTop: 0}}>Documents</h2>

            <div style={{display: "grid", gap: 10, border: "1px solid #ddd", padding: 12, borderRadius: 12}}>
                <label>
                    Doc ID (optional)
                    <input
                        value={docId}
                        onChange={(e) => setDocId(e.target.value)}
                        placeholder="e.g. onboarding-notes"
                        style={{
                            width: "100%",
                            height: 40,
                            borderRadius: 10,
                            border: "1px solid #ddd",
                            padding: "0 12px"
                        }}
                    />
                </label>

                <input
                    type="file"
                    accept=".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                />

                <button onClick={upload} disabled={busy || !file} style={{height: 44}}>
                    {busy ? "Uploading…" : "Upload & Index"}
                </button>
                <button onClick={refreshList} disabled={loadingList} style={{height: 44}}>
                    {loadingList ? "Refreshing…" : "Refresh list"}
                </button>

                {status && <div style={{color: status.startsWith("✅") ? "green" : "#b91c1c"}}>{status}</div>}
                <button onClick={chatPage}>Chat Page</button>

                <div style={{marginTop: 16, border: "1px solid #ddd", borderRadius: 12, overflow: "hidden"}}>
                    <div style={{
                        padding: 12,
                        borderBottom: "1px solid #ddd",
                        display: "flex",
                        justifyContent: "space-between"
                    }}>
                        <strong>Your indexed docs</strong>
                        <span style={{color: "#666"}}>{docs.length} docs</span>
                    </div>

                    {docs.length === 0 ? (
                        <div style={{padding: 12, color: "#666"}}>No documents indexed yet.</div>
                    ) : (
                        <div style={{width: "100%"}}>
                            {docs.map((d) => (
                                <div
                                    key={d.doc_id}
                                    style={{
                                        display: "grid",
                                        gridTemplateColumns: "1fr 120px 1fr 100px",
                                        gap: 10,
                                        padding: 12,
                                        borderTop: "1px solid #eee",
                                        alignItems: "center",
                                    }}
                                >
                                    <div>
                                        <div style={{fontWeight: 600}}>{d.doc_id}</div>
                                    </div>
                                    <div style={{color: "#111"}}>{d.chunks} chunks</div>
                                    <div style={{
                                        color: "#666",
                                        overflow: "hidden",
                                        textOverflow: "ellipsis",
                                        whiteSpace: "nowrap"
                                    }}>
                                        {d.source || ""}
                                    </div>
                                    <button onClick={() => del(d.doc_id)} style={{height: 36}}>
                                        Delete
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
