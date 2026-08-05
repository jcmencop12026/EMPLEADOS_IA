import { useEffect, useState } from "react";
import { api, UserMe } from "../api";

export function HomePage() {
  const [user, setUser] = useState<UserMe | null>(null);

  useEffect(() => {
    api<UserMe>("/api/auth/me").then(setUser).catch(() => setUser(null));
  }, []);

  return (
    <div>
      <h2>Inicio</h2>
      {user ? (
        <p>
          Sesión: <strong>{user.username}</strong> ({user.role}) —{" "}
          {user.organization_name}
        </p>
      ) : (
        <p>Cargando…</p>
      )}
      <p className="muted">
        Siguiente: B2 capacidades · B3 AI Gateway (Ollama) · B4 Empleados IA
      </p>
    </div>
  );
}
