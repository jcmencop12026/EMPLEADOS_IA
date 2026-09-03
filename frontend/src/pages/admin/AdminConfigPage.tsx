import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ApiError, fetchOrgConfig, updateOrgConfig, type OrgConfig } from "../../api";
import { EnterpriseLogoField } from "../../components/admin/EnterpriseLogoField";
import { BrandMark } from "../../components/identity/BrandMark";
import { ErrorState, LoadingState } from "../../components/AsyncState";
import { ENTERPRISE_IDENTITY_EVENT } from "../../lib/brand";

const TABS = [
  { id: "general", label: "General" },
  { id: "identidad", label: "Identidad" },
  { id: "servicios", label: "Servicios" },
  { id: "ia", label: "IA" },
  { id: "integraciones", label: "Integraciones" },
  { id: "seguridad", label: "Seguridad" },
  { id: "notificaciones", label: "Notificaciones" },
  { id: "experiencia", label: "Experiencia" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export function AdminConfigPage() {
  const [config, setConfig] = useState<OrgConfig | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [tab, setTab] = useState<TabId>("general");
  const [msg, setMsg] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    fetchOrgConfig()
      .then(setConfig)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Error al cargar configuración"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  async function save(e?: React.FormEvent) {
    e?.preventDefault();
    if (!config) return;
    setSaving(true);
    setMsg(null);
    try {
      const updated = await updateOrgConfig(config);
      setConfig(updated);
      window.dispatchEvent(new Event(ENTERPRISE_IDENTITY_EVENT));
      setMsg("Configuración guardada.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo guardar");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <LoadingState message="Cargando configuración…" />;
  if (error && !config) return <ErrorState message={error} onRetry={load} />;
  if (!config) return null;

  return (
    <div className="ops-page config-page">
      <header className="page-header compact">
        <h1>Configuración</h1>
        <p className="muted">Parámetros de la organización. EIAAX permanece como plataforma madre.</p>
      </header>

      <nav className="tab-bar compact-tabs config-tabs" aria-label="Secciones de configuración">
        {TABS.map((t) => (
          <button key={t.id} type="button" className={`tab-btn ${tab === t.id ? "active" : ""}`} onClick={() => setTab(t.id)}>
            {t.label}
          </button>
        ))}
      </nav>

      <form className="panel compact-panel config-form" onSubmit={save}>
        {tab === "general" && (
          <div className="config-grid">
            <label className="config-field">Idioma
              <select className="config-input-sm" value={config.language} onChange={(e) => setConfig({ ...config, language: e.target.value })}>
                <option value="es">Español</option>
              </select>
            </label>
            <label className="config-field">Zona horaria
              <input className="config-input-md" value={config.timezone} onChange={(e) => setConfig({ ...config, timezone: e.target.value })} />
            </label>
            <label className="config-field">Formato fecha
              <select className="config-input-sm" value={config.date_format} onChange={(e) => setConfig({ ...config, date_format: e.target.value })}>
                <option value="DD/MM/YYYY">DD/MM/YYYY</option>
                <option value="YYYY-MM-DD">YYYY-MM-DD</option>
              </select>
            </label>
            <label className="config-field">Formato hora
              <select className="config-input-sm" value={config.time_format} onChange={(e) => setConfig({ ...config, time_format: e.target.value })}>
                <option value="24h">24 horas</option>
                <option value="12h">12 horas</option>
              </select>
            </label>
          </div>
        )}

        {tab === "identidad" && (
          <div className="config-identidad">
            <div className="config-brand-mother">
              <BrandMark level="micro" />
              <p className="muted small">Marca madre EIAAX — no sustituible por la identidad tenant.</p>
            </div>
            <label className="config-field">Nombre visible de la empresa
              <input
                className="config-input-lg"
                value={config.enterprise_display_name ?? ""}
                onChange={(e) => setConfig({ ...config, enterprise_display_name: e.target.value })}
                placeholder="Nombre comercial"
              />
            </label>
            <EnterpriseLogoField
              label="Logo principal"
              value={config.enterprise_logo_url ?? ""}
              onChange={(v) => setConfig({ ...config, enterprise_logo_url: v })}
            />
            <EnterpriseLogoField
              label="Logo abreviado"
              value={config.enterprise_logo_compact_url ?? ""}
              onChange={(v) => setConfig({ ...config, enterprise_logo_compact_url: v })}
              compact
            />
            <label className="config-field">Color de acento
              <input
                className="config-input-sm"
                value={config.enterprise_accent_color ?? ""}
                onChange={(e) => setConfig({ ...config, enterprise_accent_color: e.target.value })}
                placeholder="#1d4ed8"
              />
            </label>
            <p className="muted small">La identidad de informes hereda logo y nombre configurados aquí.</p>
          </div>
        )}

        {tab === "servicios" && (
          <div className="config-links-panel">
            <p className="muted">Servicios y continuidad operativa de la plataforma.</p>
            <Link className="btn secondary" to="/continuidad">Continuidad y respaldos</Link>
            <Link className="btn secondary" to="/soporte">Mesa de Ayuda</Link>
            <Link className="btn secondary" to="/administracion/proveedores-ia">Proveedores IA</Link>
          </div>
        )}

        {tab === "ia" && (
          <div className="config-links-panel">
            <p className="muted">Modelos, proveedores y políticas de inferencia.</p>
            <Link className="btn secondary" to="/administracion/proveedores-ia">Proveedores IA</Link>
            <Link className="btn secondary" to="/costos-valor">Costos y valor FinOps</Link>
            <Link className="btn secondary" to="/aprendizaje">Aprendizaje</Link>
          </div>
        )}

        {tab === "integraciones" && (
          <div className="config-links-panel">
            <p className="muted">Conectores y cableado empresarial.</p>
            <Link className="btn secondary" to="/integraciones">Integraciones</Link>
            <Link className="btn secondary" to="/integraciones/trazabilidad">Trazabilidad</Link>
          </div>
        )}

        {tab === "seguridad" && (
          <div className="config-links-panel">
            <p className="muted">Seguridad, roles y acceso empresarial.</p>
            <Link className="btn secondary" to="/administracion/seguridad">Seguridad</Link>
            <Link className="btn secondary" to="/administracion/identidad">Identidad empresarial / SSO</Link>
            <Link className="btn secondary" to="/administracion/roles">Roles y permisos</Link>
            <Link className="btn secondary" to="/mi-seguridad">Mi seguridad</Link>
          </div>
        )}

        {tab === "notificaciones" && (
          <div className="config-links-panel">
            <p className="muted">Alertas y centro de notificaciones.</p>
            <Link className="btn secondary" to="/notificaciones">Notificaciones</Link>
            <Link className="btn secondary" to="/comunicaciones">Comunicaciones</Link>
          </div>
        )}

        {tab === "experiencia" && (
          <div className="config-links-panel">
            <p className="muted">Ayuda, guía operativa y presentación.</p>
            <Link className="btn secondary" to="/ayuda/guia">Guía rápida EIAAX</Link>
            <Link className="btn secondary" to="/">Centro de Control</Link>
          </div>
        )}

        {error && <p className="error">{error}</p>}
        {msg && <p className="success">{msg}</p>}
        <div className="ops-actions">
          <button type="submit" className="btn primary" disabled={saving}>{saving ? "Guardando…" : "Guardar cambios"}</button>
        </div>
      </form>
    </div>
  );
}
