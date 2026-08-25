import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { clearToken } from "./api";

const NAV = [
  { to: "/", label: "Inicio", end: true },
  { to: "/operaciones", label: "Centro Operaciones" },
  { to: "/salud/diagnostico", label: "Diagnóstico IPS" },
  { to: "/ejecuciones", label: "Ejecuciones" },
  { to: "/directorio", label: "Directorio" },
  { to: "/organizacion", label: "Organización" },
  { to: "/auditoria", label: "Auditoría" },
];

export function AppShell() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className={`layout ${collapsed ? "sidebar-collapsed" : ""}`}>
      <aside className="sidebar" title="Navegación principal">
        <div className="brand-row">
          <div className="brand">Enterprise AI OS</div>
          <button
            type="button"
            className="btn-icon"
            title={collapsed ? "Expandir menú" : "Colapsar menú"}
            onClick={() => setCollapsed((c) => !c)}
          >
            {collapsed ? "»" : "«"}
          </button>
        </div>
        <nav>
          {NAV.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end} title={item.label}>
              <span className="nav-icon">●</span>
              <span className="nav-label">{item.label}</span>
            </NavLink>
          ))}
        </nav>
        <button
          type="button"
          className="btn-link"
          title="Cerrar sesión"
          onClick={() => {
            clearToken();
            window.location.href = "/login";
          }}
        >
          <span className="nav-icon">⎋</span>
          <span className="nav-label">Cerrar sesión</span>
        </button>
      </aside>
      <div className="main">
        <header className="topbar">
          EMPLEADOS_IA · Orquestador E2E · Workspace Salud
        </header>
        <section className="content">
          <Outlet />
        </section>
      </div>
    </div>
  );
}
