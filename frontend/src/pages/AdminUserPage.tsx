import {useEffect, useState} from "react";
import {type AdminUser, createUser, deleteUser, listUsers} from "../api/adminUsers";
import {useNavigate} from "react-router-dom";

export default function AdminUsersPage() {
    const navigate = useNavigate();
    const [users, setUsers] = useState<AdminUser[]>([]);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState("");
    const [form, setForm] = useState({
        email: "",
        password: "",
        confirm_password: "",
        is_admin: false,
    });

    async function loadUsers() {
        try {
            setLoading(true);
            setError("");
            const data = await listUsers();
            setUsers(data);
        } catch (err: any) {
            setError(err?.response?.data?.detail || "Failed to load users");
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        loadUsers();
    }, []);

    async function handleCreate(e: React.FormEvent) {
        e.preventDefault();
        if (form.password === form.confirm_password) {
            try {
                setSubmitting(true);
                setError("");

                await createUser(form);

                setForm({
                    email: "",
                    password: "",
                    confirm_password: "",
                    is_admin: false,
                });

                await loadUsers();
            } catch (err: any) {
                setError(err?.response?.data?.detail || "Failed to create user");
            } finally {
                setSubmitting(false);
            }
        } else {
            setError('Error with password verification')
        }

    }

    async function handleDelete(userId: number) {
        const confirmed = window.confirm("Delete this user?");
        if (!confirmed) return;

        try {
            setError("");
            await deleteUser(userId);
            await loadUsers();
        } catch (err: any) {
            setError(err?.response?.data?.detail || "Failed to delete user");
        }
    }

    function chatPage() {
        navigate("/chat", {replace: true})
    }

    return (
        <div style={{padding: 24, maxWidth: 1100, margin: "0 auto"}}>
            <button style={{
                padding: "10px 14px",
                borderRadius: 8,
                border: "none",
                cursor: "pointer",
            }} onClick={chatPage}>Chat Page
            </button>
            <h1>User Management</h1>
            <p>Create, view, and delete users.</p>

            {error ? (
                <div
                    style={{
                        background: "#fee2e2",
                        color: "#991b1b",
                        padding: 12,
                        borderRadius: 8,
                        marginBottom: 16,
                    }}
                >
                    {error}
                </div>
            ) : null}

            <form
                onSubmit={handleCreate}
                style={{
                    display: "grid",
                    gap: 12,
                    padding: 16,
                    border: "1px solid #ddd",
                    borderRadius: 12,
                    marginBottom: 24,
                }}
            >
                <h2 style={{margin: 0}}>Create User</h2>

                <input
                    type="email"
                    placeholder="Email"
                    value={form.email}
                    onChange={(e) => setForm((prev) => ({...prev, email: e.target.value}))}
                    required
                    style={{padding: 10, borderRadius: 8, border: "1px solid #ccc"}}
                />

                <input
                    type="password"
                    placeholder="Password"
                    value={form.password}
                    onChange={(e) => setForm((prev) => ({...prev, password: e.target.value}))}
                    required
                    style={{padding: 10, borderRadius: 8, border: "1px solid #ccc"}}
                />
                <input
                    type="password"
                    placeholder="Confirm password"
                    value={form.confirm_password}
                    onChange={(e) => setForm((prev) => ({...prev, confirm_password: e.target.value}))}
                    required
                    style={{padding: 10, borderRadius: 8, border: "1px solid #ccc"}}
                />

                <label style={{display: "flex", gap: 8, alignItems: "center"}}>
                    <input
                        type="checkbox"
                        checked={form.is_admin}
                        onChange={(e) => setForm((prev) => ({...prev, is_admin: e.target.checked}))}
                    />
                    Admin user
                </label>

                <button
                    type="submit"
                    disabled={submitting}
                    style={{
                        padding: "10px 14px",
                        borderRadius: 8,
                        border: "none",
                        cursor: "pointer",
                    }}
                >
                    {submitting ? "Creating..." : "Create user"}
                </button>
            </form>

            <div
                style={{
                    border: "1px solid #ddd",
                    borderRadius: 12,
                    overflow: "hidden",
                }}
            >
                <div style={{padding: 16, borderBottom: "1px solid #ddd"}}>
                    <h2 style={{margin: 0}}>All Users</h2>
                </div>

                {loading ? (
                    <div style={{padding: 16}}>Loading users...</div>
                ) : users.length === 0 ? (
                    <div style={{padding: 16}}>No users found.</div>
                ) : (
                    <table style={{width: "100%", borderCollapse: "collapse"}}>
                        <thead>
                        <tr style={{textAlign: "left", borderBottom: "1px solid #ddd"}}>
                            <th style={{padding: 12}}>ID</th>
                            <th style={{padding: 12}}>Email</th>
                            <th style={{padding: 12}}>Active</th>
                            <th style={{padding: 12}}>Admin</th>
                            <th style={{padding: 12}}>Created</th>
                            <th style={{padding: 12}}>Actions</th>
                        </tr>
                        </thead>
                        <tbody>
                        {users.map((user) => (
                            <tr key={user.id} style={{borderBottom: "1px solid #eee"}}>
                                <td style={{padding: 12}}>{user.id}</td>
                                <td style={{padding: 12}}>{user.email}</td>
                                <td style={{padding: 12}}>{user.is_active ? "Yes" : "No"}</td>
                                <td style={{padding: 12}}>{user.is_admin ? "Yes" : "No"}</td>
                                <td style={{padding: 12}}>
                                    {new Date(user.created_at).toLocaleString()}
                                </td>
                                <td style={{padding: 12}}>
                                    <button
                                        onClick={() => handleDelete(user.id)}
                                        style={{
                                            padding: "8px 12px",
                                            borderRadius: 8,
                                            border: "1px solid #ccc",
                                            cursor: "pointer",
                                        }}
                                    >
                                        Delete
                                    </button>
                                </td>
                            </tr>
                        ))}
                        </tbody>
                    </table>
                )}
            </div>

        </div>
    );
}