import {type PropsWithChildren, useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { isAccessTokenValid, clearTokens } from "../api/auth";
import { refreshAccessToken } from "../api/authApi";


export default function ProtectedRoute({ children }: PropsWithChildren) {
  const location = useLocation();
  const [allowed, setAllowed] = useState<boolean | null>(null);

  useEffect(() => {
    let alive = true;

    async function check() {
      if (isAccessTokenValid()) {
        if (alive) setAllowed(true);
        return;
      }

      const newAccess = await refreshAccessToken();
      if (alive) setAllowed(!!newAccess);
      if (!newAccess) clearTokens();
    }

    check();
    return () => {
      alive = false;
    };
  }, []);

  // loading state while checking/refreshing
  if (allowed === null) return <div style={{ padding: 16 }}>Checking session…</div>;

  if (!allowed) {
    return <Navigate to="/auth" replace state={{ from: location }} />;
  }

  return children;
}
