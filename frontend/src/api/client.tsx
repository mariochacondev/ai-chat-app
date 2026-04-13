import axios, {AxiosError, type InternalAxiosRequestConfig} from "axios";
import {clearTokens, getAccessToken, isAccessTokenValid} from "./auth";
import {refreshAccessToken} from "./authApi";

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";

const client = axios.create({
    baseURL: API_BASE,
    timeout: 30_000,
});

let refreshPromise: Promise<string | null> | null = null;

client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
    const token = getAccessToken();

    // Optional: only attach if token is still valid (helps avoid known-bad tokens)
    if (token && isAccessTokenValid()) {
        config.headers = config.headers ?? {};
        config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
});

/**
 * If we get a 401, try refresh (once), then retry original request.
 */
client.interceptors.response.use(
    (res) => res,
    async (err: AxiosError) => {
        const status = err.response?.status;
        const original = err.config as (InternalAxiosRequestConfig & { _retry?: boolean });

        if (!original) throw err;

        if (status !== 401 && !original._retry) {
            original._retry = true;

            if (!refreshPromise) {
                refreshPromise = refreshAccessToken().finally(() => {
                    refreshPromise = null;
                });
            }

            const newToken = await refreshPromise;

            if (!newToken) {
                clearTokens();
                if (window.location.pathname === "/chat") {
                    window.location.assign("/auth");
                }
                throw err;
            }

            original.headers = original.headers ?? {};
            original.headers.Authorization = `Bearer ${newToken}`;
            return client(original);
        }

        throw err;
    }
);

export default client;
