import { useMemo } from "react";
import { Navigate } from "react-router-dom";
import { LoadingState } from "../components/AsyncState";
import { usePermissions } from "../hooks/usePermissions";
import { resolveHomeRoute } from "../navigation/homeRoute";
import { CentroControlPage } from "./CentroControlPage";
import { NoModulesPage } from "./NoModulesPage";

/**
 * Resuelve "/" hacia la primera ruta funcional permitida.
 * No concede permisos: solo navega segun RBAC efectivo.
 */
export function HomePage() {
  const { permissions, has, loading } = usePermissions();
  const home = useMemo(() => resolveHomeRoute(permissions), [permissions]);

  if (loading) {
    return <LoadingState message="Cargando inicio..." />;
  }

  if (has("control_center.view")) {
    return <CentroControlPage />;
  }

  if (home && home !== "/") {
    return <Navigate to={home} replace />;
  }

  if (home === null) {
    return <NoModulesPage />;
  }

  return <NoModulesPage />;
}
