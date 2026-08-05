import { NavLink, Outlet } from "react-router-dom";
import { clearToken } from "./api";

export function AppShell() {
  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">Enterprise AI OS</div>
        <nav>
          <NavLink to="/" end>
            Inicio
          </NavLink>
          <NavLink to="/organizacion">Organización</NavLink>
          <NavLink to="/auditoria">Auditoría</NavLink>
        </nav>
        <button
          type="button"
          className="btn-link"
          onClick={() => {
            clearToken();
            window.location.href = "/login";
          }}
        >
          Cerrar sesión
        </button>
      </aside>
      <div className="main">
        <header className="topbar">EMPLEADOS_IA · Núcleo B1</header>
        <section className="content">
          <Outlet />
        </section>
      </div>
    </div>
  );
}
