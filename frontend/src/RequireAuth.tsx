import { useEffect, useState } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { getToken } from "./api";
import { validateSession } from "./auth/session";
import { LoadingState } from "./components/AsyncState";

export function RequireAuth() {
  const location = useLocation();
  const [ready, setReady] = useState(false);
  const [valid, setValid] = useState(false);

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
  }, [location.pathname]);

  if (!ready) {
    return <LoadingState message="Verificando sesión…" />;
  }
  if (!valid) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  return <Outlet />;
}
