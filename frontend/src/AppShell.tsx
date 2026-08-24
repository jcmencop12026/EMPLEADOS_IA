import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { clearToken, fetchUnreadCount } from "./api";

const NAV = [
  { to: "/", label: "Inicio", end: true },
  { to: "/operaciones", label: "Centro Operaciones" },
  { to: "/ejecuciones", label: "Ejecuciones" },
  { to: "/directorio", label: "Directorio" },
  { to: "/organizacion", label: "Organización" },
  { to: "/auditoria", label: "Auditoría" },
  { to: "/notificaciones", label: "Notificaciones" },
];

export function AppShell() {
  const [collapsed, setCollapsed] = useState(false);
  const [unread, setUnread] = useState(0);
  useEffect(() => {
    const refresh = () => fetchUnreadCount().then(setUnread).catch(() => undefined);
    refresh();
    const timer = window.setInterval(refresh, 60000);
    window.addEventListener("notifications-changed", refresh);
    return () => { window.clearInterval(timer); window.removeEventListener("notifications-changed", refresh); };
  }, []);

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
          <span>EMPLEADOS_IA · Orquestador E2E · Workspace Salud</span>
          <NavLink className="notification-bell" to="/notificaciones" title="Centro de notificaciones">
            🔔{unread > 0 && <span className="notification-badge">{unread > 99 ? "99+" : unread}</span>}
          </NavLink>
        </header>
        <section className="content">
          <Outlet />
        </section>
      </div>
    </div>
  );
}
