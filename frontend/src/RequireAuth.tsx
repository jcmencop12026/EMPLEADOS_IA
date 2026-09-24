import { useEffect, useState } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { getToken } from "./api";
import { getCachedUser, validateSession } from "./auth/session";
import { LoadingState } from "./components/AsyncState";

export function RequireAuth() {
  const location = useLocation();
  const cached = Boolean(getToken() && getCachedUser());
  const [ready, setReady] = useState(cached);
  const [valid, setValid] = useState(cached);

  useEffect(() => {
    if (!getToken()) {
      setValid(false);
      setReady(true);
      return;
    }
    validateSession()
      .then(() => {
        setValid(true);
        setReady(true);
      })
      .catch(() => {
        setValid(false);
        setReady(true);
      });
  }, []);

  if (!ready) {
    return <LoadingState message="Verificando sesión…" />;
  }
  if (!valid) {
    const next = `${location.pathname}${location.search}${location.hash}`;
    return <Navigate to={`/login?next=${encodeURIComponent(next)}`} replace state={{ from: location }} />;
  }
  return <Outlet />;
}
