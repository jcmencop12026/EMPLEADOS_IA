import { logout } from "../auth/session";

export function NoModulesPage() {
  return (
    <div className="ops-page">
      <div className="login-card" style={{ maxWidth: 480, margin: "2rem auto" }}>
        <h1>Sin módulos habilitados</h1>
        <p className="muted">
          No tiene módulos habilitados para su usuario. Contacte al administrador de su organización.
        </p>
        <button type="button" onClick={logout}>
          Cerrar sesión
        </button>
      </div>
    </div>
  );
}
