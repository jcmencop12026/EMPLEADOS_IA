import { useCallback, useEffect, useState } from "react";
import {
  activateIdentityProvider,
  createIdentityProvider,
  fetchIdentityEvents,
  fetchIdentityPolicy,
  fetchIdentityProviders,
  testIdentityProvider,
  updateIdentityPolicy,
  upsertGroupRoleMapping,
  type IdentityLoginEvent,
  type IdentityPolicy,
  type IdentityProvider,
} from "../../api";
import { ErrorState, LoadingState } from "../../components/AsyncState";

const STATUS_LABELS: Record<string, string> = {
  BORRADOR: "Borrador",
  CONFIGURADO: "Configurado",
  VERIFICADO: "Verificado",
  ACTIVO: "Activo",
  ERROR: "Error",
  DESHABILITADO: "Deshabilitado",
};

const AUTH_MODE_LABELS: Record<string, string> = {
  SOLO_LOCAL: "Solo local",
  LOCAL_Y_SSO: "Local y SSO",
  SOLO_SSO: "Solo SSO",
};

export function AdminIdentidadPage() {
  const [policy, setPolicy] = useState<IdentityPolicy | null>(null);
  const [providers, setProviders] = useState<IdentityProvider[]>([]);
  const [events, setEvents] = useState<IdentityLoginEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [newCode, setNewCode] = useState("");
  const [newName, setNewName] = useState("");
  const [newType, setNewType] = useState("OIDC");

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([fetchIdentityPolicy(), fetchIdentityProviders(), fetchIdentityEvents(30)])
      .then(([pol, prov, ev]) => {
        setPolicy(pol);
        setProviders(prov);
        setEvents(ev);
        setError(null);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar identidad"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function onSavePolicy() {
    if (!policy) return;
    setMessage(null);
    try {
      const updated = await updateIdentityPolicy(policy);
      setPolicy(updated);
      setMessage("Política de identidad actualizada.");
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "No se pudo guardar.");
    }
  }

  async function onCreateProvider() {
    setMessage(null);
    try {
      await createIdentityProvider({
        code: newCode,
        name: newName,
        provider_type: newType,
        config: newType === "OIDC"
          ? { issuer: "https://idp.ejemplo.com", client_id: "client-id", mock_discovery: { authorization_endpoint: "https://idp.ejemplo.com/auth" } }
          : { sso_url: "https://idp.ejemplo.com/saml", mock_saml_redirect: true },
      });
      setNewCode("");
      setNewName("");
      load();
      setMessage("Proveedor creado en borrador.");
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "No se pudo crear el proveedor.");
    }
  }

  if (loading) return <LoadingState message="Cargando identidad empresarial…" />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!policy) return null;

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Identidad empresarial</h1>
        <p className="muted">SSO, OIDC, SAML, mapeos y políticas de autenticación</p>
      </header>

      {message && <p className="panel" role="status">{message}</p>}

      <section className="panel">
        <h2>Políticas de autenticación</h2>
        <div className="form-stack">
          <label>
            Modo de autenticación
            <select value={policy.auth_mode} onChange={(e) => setPolicy({ ...policy, auth_mode: e.target.value })}>
              {Object.entries(AUTH_MODE_LABELS).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </label>
          <label>
            MFA con SSO
            <select value={policy.mfa_sso_mode} onChange={(e) => setPolicy({ ...policy, mfa_sso_mode: e.target.value })}>
              <option value="EAIOS">Gestionado por EMPLEADOS IA</option>
              <option value="IDP">Confiado al proveedor de identidad</option>
              <option value="ADICIONAL">MFA adicional requerido</option>
            </select>
          </label>
          <label>
            <input
              type="checkbox"
              checked={policy.auto_provision_enabled}
              onChange={(e) => setPolicy({ ...policy, auto_provision_enabled: e.target.checked })}
            />
            {" "}Auto-provisión en primer login
          </label>
          <label>
            Código de descubrimiento (login)
            <input value={policy.org_discovery_code || ""} onChange={(e) => setPolicy({ ...policy, org_discovery_code: e.target.value })} />
          </label>
          <button type="button" onClick={onSavePolicy}>Guardar política</button>
        </div>
      </section>

      <section className="panel">
        <h2>Proveedores de identidad</h2>
        <div className="form-stack" style={{ marginBottom: "1rem" }}>
          <input placeholder="Código" value={newCode} onChange={(e) => setNewCode(e.target.value)} />
          <input placeholder="Nombre" value={newName} onChange={(e) => setNewName(e.target.value)} />
          <select value={newType} onChange={(e) => setNewType(e.target.value)}>
            <option value="OIDC">OIDC / OpenID Connect</option>
            <option value="SAML">SAML 2.0</option>
          </select>
          <button type="button" onClick={onCreateProvider}>Nuevo proveedor</button>
        </div>
        <table className="data-table">
          <thead>
            <tr><th>Nombre</th><th>Tipo</th><th>Estado</th><th>Secreto</th><th>Acciones</th></tr>
          </thead>
          <tbody>
            {providers.map((p) => (
              <tr key={p.id}>
                <td>{p.name}</td>
                <td>{p.provider_type}</td>
                <td>{STATUS_LABELS[p.status] ?? p.status}</td>
                <td>{p.secret_configured ? "Configurado" : "No configurado"}</td>
                <td className="button-row">
                  <button type="button" onClick={() => testIdentityProvider(p.id).then(load)}>Probar</button>
                  <button type="button" onClick={() => activateIdentityProvider(p.id).then(load)}>Activar</button>
                  <button
                    type="button"
                    onClick={() => upsertGroupRoleMapping(p.id, { external_group: "equipo-ops", role_code: "viewer" }).then(load)}
                  >
                    Mapeo ejemplo
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="panel">
        <h2>Eventos de login</h2>
        <table className="data-table">
          <thead><tr><th>Fecha</th><th>Método</th><th>Resultado</th><th>Detalle</th></tr></thead>
          <tbody>
            {events.map((ev) => (
              <tr key={ev.id}>
                <td>{new Date(ev.created_at).toLocaleString("es-CO")}</td>
                <td>{ev.login_method}</td>
                <td>{ev.result}</td>
                <td className="cell-truncate">{ev.detail || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
