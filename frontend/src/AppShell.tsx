import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { clearToken } from "./api";

const NAV = [
  { to: "/", label: "Inicio", end: true },
  { to: "/operaciones", label: "Centro Operaciones" },
  { to: "/ejecuciones", label: "Ejecuciones" },
  { to: "/directorio", label: "Directorio" },
  { to: "/auditoria", label: "Auditoría" },
];

const ADMIN_NAV = [
  { to: "/administracion/usuarios", label: "Usuarios" },
  { to: "/administracion/roles", label: "Roles y permisos" },
  { to: "/administracion/organizacion", label: "Organización" },
  { to: "/administracion/configuracion", label: "Configuración" },
  { to: "/administracion/seguridad", label: "Seguridad" },
];

export function AppShell() {
  const [collapsed, setCollapsed] = useState(false);
  const [adminOpen, setAdminOpen] = useState(true);

  return (
    <div className={`layout ${collapsed ? "sidebar-collapsed" : ""}`}>
      <aside className="sidebar" title="Navegación principal">
        <div className="brand-row">
          <div className="brand">Enterprise AI OS</div>
          <button type="button" className="btn-icon" title={collapsed ? "Expandir menú" : "Colapsar menú"} onClick={() => setCollapsed((c) => !c)}>
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
          <div className="nav-section">
            <button type="button" className="nav-section-title" onClick={() => setAdminOpen((o) => !o)}>
              <span className="nav-icon">{adminOpen ? "▾" : "▸"}</span>
              <span className="nav-label">Administración</span>
            </button>
            {adminOpen && ADMIN_NAV.map((item) => (
              <NavLink key={item.to} to={item.to} title={item.label} className="nav-sub">
                <span className="nav-icon">○</span>
                <span className="nav-label">{item.label}</span>
              </NavLink>
            ))}
          </div>
        </nav>
        <button type="button" className="btn-link" title="Cerrar sesión" onClick={() => { clearToken(); window.location.href = "/login"; }}>
          <span className="nav-icon">⎋</span>
          <span className="nav-label">Cerrar sesión</span>
        </button>
      </aside>
      <div className="main">
        <header className="topbar">EMPLEADOS_IA · Orquestador E2E · Workspace Salud</header>
        <section className="content">
          <Outlet />
        </section>
      </div>
    </div>
  );
}
