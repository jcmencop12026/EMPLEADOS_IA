import { useEffect, useMemo, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { fetchUnreadCount } from "./api";
import { filterMenuByPermissions } from "./auth/permissions";
import { getCachedUser, logout } from "./auth/session";

type NavItem = { to: string; label: string; end?: boolean };
type NavSection = { id: string; label: string; items: NavItem[]; future?: boolean };

const MENU: NavSection[] = [
  {
    id: "inicio",
    label: "Inicio",
    items: [{ to: "/", label: "Panel de control", end: true }],
  },
  {
    id: "operaciones",
    label: "Operaciones",
    items: [
      { to: "/operaciones", label: "Centro de operaciones" },
      { to: "/ejecuciones", label: "Ejecuciones" },
      { to: "/aprobaciones", label: "Aprobaciones" },
      { to: "/automatizaciones", label: "Automatizaciones" },
    ],
  },
  {
    id: "salud",
    label: "Salud",
    items: [{ to: "/salud/diagnostico", label: "Diagnóstico IPS" }],
  },
  {
    id: "empleados",
    label: "Empleados IA",
    items: [
      { to: "/directorio", label: "Directorio" },
      { to: "/empleados/nuevo", label: "Crear empleado" },
      { to: "/capacidades", label: "Capacidades" },
      { to: "/herramientas", label: "Herramientas" },
      { to: "/conocimiento", label: "Conocimiento" },
      { to: "/test-lab", label: "Test Lab" },
    ],
  },
  {
    id: "analisis",
    label: "Análisis y control",
    items: [
      { to: "/lineas-base", label: "Líneas base e impacto" },
      { to: "/oportunidades", label: "Centro de oportunidades" },
      { to: "/senales", label: "Señales y fuentes" },
      { to: "/diagnosticos", label: "Diagnósticos" },
      { to: "/costos-valor", label: "Costos y valor" },
      { to: "/gobernanza-datos", label: "Gobierno de datos" },
      { to: "/notificaciones", label: "Notificaciones" },
      { to: "/auditoria", label: "Auditoría" },
    ],
  },
  {
    id: "admin",
    label: "Administración",
    items: [
      { to: "/administracion/empresas", label: "Empresas" },
      { to: "/administracion/usuarios", label: "Usuarios" },
      { to: "/administracion/roles", label: "Roles y permisos" },
      { to: "/administracion/organizacion", label: "Organización" },
      { to: "/administracion/configuracion", label: "Configuración" },
      { to: "/administracion/proveedores-ia", label: "Proveedores IA" },
      { to: "/administracion/seguridad", label: "Seguridad" },
    ],
  },
];

const COLLAPSE_KEY = "eaios_menu_collapsed";
const SECTION_KEY = "eaios_menu_sections";

function loadSections(): Record<string, boolean> {
  try {
    return JSON.parse(localStorage.getItem(SECTION_KEY) || "{}") as Record<string, boolean>;
  } catch {
    return {};
  }
}

export function AppShell() {
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem(COLLAPSE_KEY) === "1");
  const [sections, setSections] = useState<Record<string, boolean>>(loadSections);
  const [unread, setUnread] = useState(0);
  const user = getCachedUser();
  const permissionSet = useMemo(
    () => new Set(user?.permissions ?? []),
    [user?.permissions],
  );

  const visibleMenu = useMemo(
    () =>
      MENU.map((section) => ({
        ...section,
        items: filterMenuByPermissions(section.items, permissionSet),
      })).filter((section) => section.items.length > 0),
    [permissionSet],
  );

  useEffect(() => {
    localStorage.setItem(COLLAPSE_KEY, collapsed ? "1" : "0");
  }, [collapsed]);

  useEffect(() => {
    localStorage.setItem(SECTION_KEY, JSON.stringify(sections));
  }, [sections]);

  useEffect(() => {
    const refresh = () => fetchUnreadCount().then(setUnread).catch(() => undefined);
    refresh();
    const timer = window.setInterval(refresh, 60000);
    window.addEventListener("notifications-changed", refresh);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener("notifications-changed", refresh);
    };
  }, []);

  function toggleSection(id: string) {
    setSections((prev) => ({ ...prev, [id]: !(prev[id] ?? true) }));
  }

  const isOpen = (id: string) => sections[id] ?? true;

  function renderSection(section: NavSection) {
    const open = isOpen(section.id);
    return (
      <div key={section.id} className={`nav-section ${section.future ? "nav-section-future" : ""}`}>
        <button
          type="button"
          className="nav-section-title"
          onClick={() => toggleSection(section.id)}
          title={section.label}
        >
          <span className="nav-icon">{open ? "▾" : "▸"}</span>
          <span className="nav-label">{section.label}</span>
        </button>
        {open && (
          <div className="nav-section-items">
            {section.items.map((item) =>
              section.future || item.to === "#" ? (
                <span key={item.label} className="nav-future" title="Integración pendiente">
                  <span className="nav-icon">○</span>
                  <span className="nav-label">{item.label}</span>
                </span>
              ) : (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  title={item.label}
                  className={section.id === "admin" ? "nav-sub" : undefined}
                >
                  <span className="nav-icon">{section.id === "admin" ? "○" : "●"}</span>
                  <span className="nav-label">{item.label}</span>
                </NavLink>
              ),
            )}
          </div>
        )}
      </div>
    );
  }

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
        <nav className="nav-hierarchical">
          {visibleMenu.map(renderSection)}
        </nav>
        <div className="sidebar-footer">
          {user && (
            <div className="sidebar-user" title={`${user.username} · ${user.organization_name}`}>
              <span className="nav-icon">◉</span>
              <span className="nav-label">{user.username}</span>
            </div>
          )}
          <button type="button" className="btn-link" title="Cerrar sesión" onClick={logout}>
            <span className="nav-icon">⎋</span>
            <span className="nav-label">Cerrar sesión</span>
          </button>
        </div>
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
