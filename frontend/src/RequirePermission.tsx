import { Navigate, Outlet } from "react-router-dom";
import { getCachedUser } from "./auth/session";

type RequirePermissionProps = {
  anyOf: string[];
  redirectTo?: string;
};

export function RequirePermission({ anyOf, redirectTo = "/" }: RequirePermissionProps) {
  const user = getCachedUser();
  if (!user) return <Navigate to="/login" replace />;
  const permissions = new Set(user.permissions ?? []);
  const allowed = anyOf.some((code) => permissions.has(code));
  return allowed ? <Outlet /> : <Navigate to={redirectTo} replace />;
}
