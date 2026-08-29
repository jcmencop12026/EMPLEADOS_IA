import { useEffect, useState } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { LoadingState } from "./components/AsyncState";
import { getCachedUser, validateSession } from "./auth/session";

type RequirePermissionProps = {
  anyOf: string[];
  redirectTo?: string;
};

export function RequirePermission({ anyOf, redirectTo = "/" }: RequirePermissionProps) {
  const [ready, setReady] = useState(false);
  const [allowed, setAllowed] = useState(false);

  useEffect(() => {
    const check = async () => {
      try {
        const user = getCachedUser() ?? (await validateSession());
        const perms = new Set(user.permissions ?? []);
        setAllowed(anyOf.some((code) => perms.has(code)));
      } catch {
        setAllowed(false);
      } finally {
        setReady(true);
      }
    };
    void check();
  }, [anyOf]);

  if (!ready) {
    return <LoadingState message="Verificando permisos…" />;
  }
  if (!allowed) {
    return <Navigate to={redirectTo} replace />;
  }
  return <Outlet />;
}
