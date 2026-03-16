import type {CSSProperties, FormEventHandler} from "react";
import {Link} from "react-router-dom";

export type RegisterProps = {
    onSubmit: FormEventHandler<HTMLFormElement>;
    email: string;
    setEmail: (v: string) => void;
    password: string;
    confirmPassword: string;
    setPassword: (v: string) => void;
    setConfirmPassword: (v: string) => void;
    error?: string | null;
    loading?: boolean;
    apiBaseUrl?: string;
    styles?: Partial<Record<StyleKey, CSSProperties>>;
};

type StyleKey =
    | "page"
    | "card"
    | "header"
    | "title"
    | "subtitle"
    | "form"
    | "label"
    | "input"
    | "errorBox"
    | "button"
    | "footer"
    | "link"
    | "hint"
    | "hintTitle"
    | "hintText";

const defaultStyles: Record<StyleKey, CSSProperties> = {
    page: {
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        padding: 24,
        background: "linear-gradient(180deg, #fafafa, #f2f2f2)",
    },
    card: {
        width: "100%",
        maxWidth: 420,
        background: "#fff",
        borderRadius: 14,
        padding: 22,
        boxShadow: "0 10px 30px rgba(0,0,0,0.08), 0 2px 10px rgba(0,0,0,0.06)",
        border: "1px solid rgba(0,0,0,0.06)",
    },
    header: {marginBottom: 16},
    title: {margin: 0, fontSize: 28, letterSpacing: -0.3},
    subtitle: {margin: "6px 0 0", color: "#666"},
    form: {display: "grid", gap: 12, marginTop: 14},
    label: {display: "grid", gap: 6, fontSize: 14, color: "#333"},
    input: {
        height: 42,
        padding: "0 12px",
        borderRadius: 10,
        border: "1px solid rgba(0,0,0,0.16)",
        outline: "none",
        fontSize: 14,
    },
    errorBox: {
        borderRadius: 10,
        padding: "10px 12px",
        background: "rgba(220, 38, 38, 0.08)",
        border: "1px solid rgba(220, 38, 38, 0.25)",
        color: "#b91c1c",
        fontSize: 14,
    },
    button: {
        height: 44,
        borderRadius: 10,
        border: "none",
        background: "#111",
        color: "#fff",
        fontWeight: 600,
        fontSize: 14,
    },
    footer: {
        marginTop: 2,
        display: "flex",
        justifyContent: "center",
        gap: 6,
        fontSize: 14,
    },
    link: {color: "#111", textDecoration: "underline"},
    hint: {
        marginTop: 16,
        paddingTop: 14,
        borderTop: "1px solid rgba(0,0,0,0.06)",
    },
    hintTitle: {fontSize: 12, fontWeight: 700, color: "#666"},
    hintText: {fontSize: 12, color: "#666", marginTop: 6},
};

export default function Login(props: RegisterProps) {
    const {
        onSubmit,
        email,
        setEmail,
        password,
        setPassword,
        confirmPassword,
        setConfirmPassword,
        error,
        loading = false,
        apiBaseUrl,
        styles,
    } = props;

    const s = {...defaultStyles, ...styles};

    return (
        <div style={s.page}>
            <div style={s.card}>
                <div style={s.header}>
                    <h1 style={s.title}>Register</h1>
                    <p style={s.subtitle}>
                        Access your AI chat workspace.
                    </p>
                </div>

                <form onSubmit={onSubmit} style={s.form}>
                    <label style={s.label}>
                        Email
                        <input
                            type="email"
                            autoComplete="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="you@example.com"
                            style={s.input}
                            required
                        />
                    </label>

                    <label style={s.label}>
                        Password
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            style={s.input}
                            required
                        />
                    </label>
                    <label style={s.label}>
                        Confirm Password
                        <input
                            type="password"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            style={s.input}
                            required
                        />
                    </label>

                    {error && (
                        <div style={s.errorBox} role="alert">
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        style={{
                            ...s.button,
                            opacity: loading ? 0.7 : 1,
                            cursor: loading ? "not-allowed" : "pointer",
                        }}
                    >
                        {loading ? "Registering and Signing in..." : "Register"}
                    </button>
                    <div style={s.footer}>
                        <span style={{color: "#666"}}>Already have an account?</span>{" "}
                        <Link to="/auth?mode=login" style={s.link}>
                            Log in
                        </Link>
                    </div>
                </form>

                <div style={s.hint}>
                    <div style={s.hintTitle}>Dev hint</div>
                    <div style={s.hintText}>
                        API base URL: <code>{apiBaseUrl}</code>
                    </div>
                </div>
            </div>
        </div>
    );
}
