import {type FormEvent, useMemo, useState} from "react";
import {useLocation, useNavigate, useSearchParams} from "react-router-dom";
import client from "../api/client";
import Login from "../components/Login";
import Register from "../components/Register"


type LoginResponse = {
    access_token: string;
    refresh_token: string;
    token_type: "bearer" | string;
};
type RegisterResponse = {
    access_token: string;
    refresh_token: string;
    token_type: "bearer" | string;
};

function getApiBaseUrl() {
    return import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";
}

export default function AuthPage() {
    const [params] = useSearchParams();
    const mode = (params.get("mode") || "login") as "login" | "register";

    const apiBaseUrl = useMemo(() => getApiBaseUrl(), []);
    const navigate = useNavigate();
    const location = useLocation();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("")

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const nextPath =
        (location.state as any)?.from?.pathname ||
        (location.state as any)?.next ||
        "/auth?mode=login";

    async function onSubmit(e: FormEvent) {
        e.preventDefault();
        setError(null);
        setLoading(true);

        try {
            if (mode === "login") {
                const res = await client.post<LoginResponse>(
                    `${apiBaseUrl}/auth/login`,
                    {email, password},
                    {headers: {"Content-Type": "application/json"}}
                );
                sessionStorage.setItem("access_token", res.data.access_token);
                sessionStorage.setItem("refresh_token", res.data.refresh_token);
                navigate("/chat", {replace: true});
            } else if (mode === "register" && password === confirmPassword) {
                const res = await client.post<RegisterResponse>(
                    `${apiBaseUrl}/auth/register`,
                    {email, password},
                    {headers: {"Content-Type": "application/json"}}
                );

                sessionStorage.setItem("access_token", res.data.access_token);
                sessionStorage.setItem("refresh_token", res.data.refresh_token);

                navigate(nextPath, {replace: true});
            }
        } catch (err: any) {
            setError(err?.response?.data?.detail || err?.message || "Auth failed");
        } finally {
            setLoading(false);
        }
    }

    return (
        <>
            {mode === "login" ? (
                <Login
                    onSubmit={onSubmit}
                    email={email}
                    setEmail={setEmail}
                    password={password}
                    setPassword={setPassword}
                    error={error}
                    loading={loading}
                    apiBaseUrl={apiBaseUrl}
                />
            ) : (
                <Register
                    onSubmit={onSubmit}
                    email={email}
                    setEmail={setEmail}
                    password={password}
                    setPassword={setPassword}
                    confirmPassword={confirmPassword}
                    setConfirmPassword={setConfirmPassword}
                    error={error}
                    loading={loading}
                    apiBaseUrl={apiBaseUrl}
                />
            )}
        </>
    );
}
