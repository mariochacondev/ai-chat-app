import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { getCurrentUser, type CurrentUser } from "../api/me";

type Props = {
  children: React.ReactNode;
};

export default function AdminRoute({ children }: Props) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [allowed, setAllowed] = useState(false);

  useEffect(() => {
    let mounted = true;

    getCurrentUser()
      .then((data) => {
        if (!mounted) return;
        setUser(data);
        setAllowed(data.is_admin);
      })
      .catch(() => {
        if (!mounted) return;
        setAllowed(false);
      })
      .finally(() => {
        if (!mounted) return;
        setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, []);

  if (loading) {
    return <div style={{ padding: 24 }}>Loading...</div>;
  }

  if (!user || !allowed) {
    return <Navigate to="/chat" replace />;
  }

  return <>{children}</>;
}