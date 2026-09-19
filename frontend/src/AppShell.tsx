import { useEffect, useMemo, useState, type CSSProperties } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { OrganizationContextBar } from "./components/OrganizationContextBar";
import { fetchTrabajoResumen, fetchUnreadCount } from "./api";
import { filterMenuByPermissions, canAccessRoute } from "./auth/permissions";
import { getCachedUser, logout } from "./auth/session";
import { OrganizationProvider, ORGANIZATION_CONTEXT_EVENT, useOrganizationContext } from "./hooks/useOrganizationContext";
import { ContextualAssistantProvider } from "./context/ContextualAssistantContext";
import { useEnterpriseIdentity } from "./hooks/useEnterpriseIdentity";
import { MENU } from "./navigation/menu";
import { BrandMark } from "./components/identity/BrandMark";
import { EnterpriseMark } from "./components/identity/EnterpriseMark";
import { ThemeToggle } from "./components/ThemeToggle";
import { EIAAX_BRAND } from "./lib/brand";
import { navIconFor } from "./lib/navIcons";

type NavSection = (typeof MENU)[number];
const COLLAPSE_KEY = "eaios_menu_collapsed";
const SECTION_KEY = "eaios_menu_sections_v2";

function loadSections(): Record<string, boolean> {
  try {
    return JSON.parse(localStorage.getItem(SECTION_KEY) || "{}") as Record<string, boolean>;
  } catch {
    return {};
  }
}

export function AppShell() {
  return (
    <OrganizationProvider>
      <ContextualAssistantProvider>
        <AppShellInner />
      </ContextualAssistantProvider>
    </OrganizationProvider>
  );
}

function AppShellInner() {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem(COLLAPSE_KEY) === "1");
  const [sections, setSections] = useState<Record<string, boolean>>(loadSections);
  const [unread, setUnread] = useState(0);
  const [trabajoPendientes, setTrabajoPendientes] = useState(0);
  const user = getCachedUser();
  const { organizationQueryParam } = useOrganizationContext();
  const { identity } = useEnterpriseIdentity();
  const permissionKey = JSON.stringify(user?.permissions ?? []);
  const permissionSet = useMemo(
    () => new Set<string>(JSON.parse(permissionKey)),
    [permissionKey],
  );
  const isExternalPortal = permissionSet.has("espacio_externo.portal") && !permissionSet.has("control_center.view");

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
    const activeSection = visibleMenu.find((section) =>
      section.items.some((item) => item.to === "/" ? location.pathname === "/" : location.pathname.startsWith(item.to)),
    );
    if (!activeSection) return;
    setSections((prev) => {
      const next = Object.fromEntries(visibleMenu.map((section) => [section.id, section.id === activeSection.id]));
      return JSON.stringify(prev) === JSON.stringify(next) ? prev : next;
    });
  }, [location.pathname, visibleMenu]);

  useEffect(() => {
    if (isExternalPortal) return;
    const refreshNotif = () => fetchUnreadCount().then(setUnread).catch(() => undefined);
    const refreshTrabajo = () => {
      if (!canAccessRoute("/trabajo", permissionSet)) return;
      fetchTrabajoResumen(organizationQueryParam)
        .then((r) => setTrabajoPendientes(r.pendientes))
        .catch(() => undefined);
    };
    const refresh = () => {
      refreshNotif();
      refreshTrabajo();
    };
    refresh();
    const timer = window.setInterval(refresh, 60000);
    window.addEventListener("notifications-changed", refresh);
    window.addEventListener(ORGANIZATION_CONTEXT_EVENT, refresh);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener("notifications-changed", refresh);
      window.removeEventListener(ORGANIZATION_CONTEXT_EVENT, refresh);
    };
  }, [permissionSet, organizationQueryParam, isExternalPortal]);

  function toggleSection(id: string) {
    setSections((prev) => {
      const willOpen = !(prev[id] ?? false);
      return Object.fromEntries(visibleMenu.map((section) => [section.id, willOpen && section.id === id]));
    });
  }

  const isOpen = (id: string) => sections[id] ?? false;

  function renderSection(section: NavSection) {
    const open = isOpen(section.id);
    return (
      <div key={section.id} className={`nav-section ${section.future ? "nav-section-future" : ""}`}>
        <button
          type="button"
          className="nav-section-title"
          onClick={() => toggleSection(section.id)}
          title={`${open ? "Contraer" : "Expandir"} sección ${section.label}`}
          data-help={`${section.label}: ${open ? "oculta" : "muestra"} las opciones de esta área. Solo se mantiene una sección abierta para aprovechar mejor el espacio de trabajo.`}
          aria-expanded={open}
        >
          <span className="nav-icon">{open ? "▾" : "▸"}</span>
          <span className="nav-label">{section.label}</span>
        </button>
        {open && (
          <div className="nav-section-items">
            {section.items.map((item) =>
              section.future || item.to === "#" ? (
                <span key={item.label} className="nav-future" title="Integración pendiente; esta opción todavía no ejecuta acciones">
                  <span className="nav-icon">○</span>
                  <span className="nav-label">{item.label}</span>
                </span>
              ) : (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  title={item.help ?? `${item.label}: abre esta opción y conserva el contexto actual de empresa o prospecto.`}
                  data-help={item.help ?? `${item.label}: aquí puede trabajar esta función conservando el contexto actual. Pase el cursor para conocer su propósito y úsela cuando necesite actuar sobre este proceso.`}
                  aria-label={item.help ? `${item.label}. ${item.help}` : item.label}
                  className={section.id === "admin" ? "nav-sub" : undefined}
                >
                  <span className="nav-icon" aria-hidden="true">{navIconFor(item.to)}</span>
                  <span className="nav-label">
                    {item.label}
                    {item.to === "/trabajo" && trabajoPendientes > 0 && (
                      <span className="notification-badge">{trabajoPendientes > 99 ? "99+" : trabajoPendientes}</span>
                    )}
                  </span>
                </NavLink>
              ),
            )}
          </div>
        )}
      </div>
    );
  }

  const accentStyle = useMemo(
    () => (identity.accentColor ? ({ "--v1-enterprise-accent": identity.accentColor } as CSSProperties) : undefined),
    [identity.accentColor],
  );

  const hasTenantLogo = Boolean(identity.logoUrl || identity.logoCompactUrl);

  return (
    <div
      className={`layout eiaax-v1-transversal eiaax-v1-experience ${collapsed ? "sidebar-collapsed" : ""}`}
      style={accentStyle}
    >
      <aside className="sidebar" title="Navegación principal EIAAX">
        <div className="brand-row" style={{ alignItems: "flex-start", gap: 8 }}>
          <div
            className="brand"
            style={{
              display: "flex",
              flex: 1,
              minWidth: 0,
              flexDirection: "column",
              gap: 7,
              alignItems: collapsed ? "center" : "stretch",
            }}
          >
            <div
              style={{
                padding: collapsed ? 5 : "8px 10px",
                borderRadius: 10,
                background: "transparent",
                boxShadow: "none",
              }}
            >
              {hasTenantLogo ? (
                <EnterpriseMark
                  variant={collapsed ? "compact" : "shell"}
                  displayName={identity.displayName}
                  logoUrl={identity.logoUrl}
                  logoCompactUrl={identity.logoCompactUrl}
                  className="sidebar-configured-brand"
                />
              ) : (
                <BrandMark
                  level={collapsed ? "ex08" : "corporativo"}
                  title={EIAAX_BRAND.title}
                  style={{ width: collapsed ? 34 : "100%", maxWidth: collapsed ? 34 : 196, height: "auto", display: "block", margin: "0 auto" }}
                />
              )}
            </div>

            {!collapsed && identity.displayName && (
              <span
                title="Organización activa"
                style={{
                  color: "#dbeafe",
                  fontSize: 12,
                  lineHeight: 1.25,
                  fontWeight: 600,
                  textAlign: "center",
                  overflowWrap: "anywhere",
                }}
              >
                {identity.displayName}
              </span>
            )}
          </div>
          <button
            type="button"
            className="btn-icon"
            title={collapsed ? "Expandir menú principal" : "Colapsar menú principal"}
            data-help={collapsed ? "Expande el menú para mostrar títulos y opciones de navegación." : "Reduce el menú lateral para ampliar el espacio disponible de la pantalla de trabajo."}
            aria-label={collapsed ? "Expandir menú principal" : "Colapsar menú principal"}
            onClick={() => setCollapsed((c) => !c)}
          >
            {collapsed ? "»" : "«"}
          </button>
        </div>
        <nav className="nav-hierarchical" aria-label="Menú principal">
          {isExternalPortal ? (
            <div className="nav-section">
              <NavLink to="/mi-espacio" className="nav-sub">
                <span className="nav-icon" aria-hidden="true">⌂</span>
                <span className="nav-label">Mi espacio</span>
              </NavLink>
            </div>
          ) : visibleMenu.map(renderSection)}
        </nav>
        <div className="sidebar-footer">
          {user && (
            <div className="sidebar-user" title={`${user.username} · ${user.organization_name}`}>
              <span className="nav-icon">◉</span>
              <span className="nav-label">{user.username}</span>
            </div>
          )}
          <button
            type="button"
            className="btn-link"
            title="Cierra la sesión actual y vuelve al acceso seguro"
            data-help="Finaliza su sesión de EIAAX en este navegador y regresa a la pantalla de acceso. Úselo al terminar o cuando cambie de usuario."
            onClick={logout}
          >
            <span className="nav-icon">⎋</span>
            <span className="nav-label">Cerrar sesión</span>
          </button>
        </div>
      </aside>
      <div className="main">
        <header className="topbar">
          <span className="topbar-title">
            {identity.displayName ? <strong>{identity.displayName}</strong> : EIAAX_BRAND.productLine}
          </span>
          <div className="topbar-actions">
            <ThemeToggle />
            {!isExternalPortal && <OrganizationContextBar />}
            {!isExternalPortal && <NavLink
              className="notification-bell"
              to="/notificaciones"
              title="Abre el Centro de notificaciones y muestra eventos que requieren su atención"
              data-help="Abre las notificaciones de EIAAX. Úselo para revisar alertas, cambios y eventos que pueden requerir atención o una decisión."
              aria-label="Centro de notificaciones"
            >
              🔔{unread > 0 && <span className="notification-badge">{unread > 99 ? "99+" : unread}</span>}
            </NavLink>}
          </div>
        </header>
        <section className="content">
          <Outlet />
        </section>
      </div>
    </div>
  );
}
