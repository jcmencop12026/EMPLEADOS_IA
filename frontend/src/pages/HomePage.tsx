import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, UserMe } from "../api";

export function HomePage() {
  const [user, setUser] = useState<UserMe | null>(null);

  useEffect(() => {
    api<UserMe>("/api/auth/me").then(setUser).catch(() => setUser(null));
  }, []);

  return (
    <div className="ops-page">
      <h2>Inicio</h2>
      {user ? (
        <p>
          Sesión: <strong>{user.username}</strong> ({user.role}) —{" "}
          {user.organization_name}
        </p>
      ) : (
        <p>Cargando…</p>
      )}
      <div className="home-links">
        <Link className="btn primary" to="/operaciones">
          Centro de Operaciones
        </Link>
        <Link className="btn" to="/ejecuciones">
          Ejecuciones
        </Link>
        <Link className="btn" to="/directorio">
          Directorio Empleados IA
        </Link>
      </div>
      <p className="muted">
        Orquestador E2E · DOCINT · RIPS · Workspace Salud
      </p>
    </div>
  );
}
