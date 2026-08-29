import { useCallback, useEffect, useState } from "react";
import {
  activateIdentityProvider,
  configureScim,
  createIdentityProvider,
  createScimToken,
  fetchIdentityEvents,
  fetchIdentityPolicy,
  fetchIdentityProviders,
  fetchScimConflicts,
  fetchScimRoleMappings,
  fetchScimStatus,
  revokeScimToken,
  rotateScimToken,
  testIdentityProvider,
  updateIdentityPolicy,
  upsertGroupRoleMapping,
  upsertScimRoleMapping,
  type IdentityLoginEvent,
  type IdentityPolicy,
  type IdentityProvider,
  type ScimConflict,
  type ScimRoleMapping,
  type ScimStatus,
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
  const [scim, setScim] = useState<ScimStatus | null>(null);
  const [scimMappings, setScimMappings] = useState<ScimRoleMapping[]>([]);
  const [scimConflicts, setScimConflicts] = useState<ScimConflict[]>([]);
  const [newScimToken, setNewScimToken] = useState<string | null>(null);
  const [scimGroup, setScimGroup] = useState("");
  const [scimRole, setScimRole] = useState("viewer");

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([
      fetchIdentityPolicy(),
      fetchIdentityProviders(),
      fetchIdentityEvents(30),
      fetchScimStatus().catch(() => null),
      fetchScimRoleMappings().catch(() => []),
      fetchScimConflicts().catch(() => []),
    ])
      .then(([pol, prov, ev, scimData, mappings, conflicts]) => {
        setPolicy(pol);
        setProviders(prov);
        setEvents(ev);
        setScim(scimData);
        setScimMappings(mappings);
        setScimConflicts(conflicts);
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

  async function onToggleScim(enabled: boolean) {
    setMessage(null);
    try {
      await configureScim({ scim_enabled: enabled });
      load();
      setMessage(enabled ? "SCIM activado." : "SCIM desactivado.");
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "No se pudo actualizar SCIM.");
    }
  }

  async function onCreateScimToken() {
    setMessage(null);
    try {
      const res = await createScimToken({ name: "Token SCIM" });
      setNewScimToken(res.token);
      load();
      setMessage(res.message);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "No se pudo generar el token.");
    }
  }

  async function onRotateScimToken(tokenId: string) {
    setMessage(null);
    try {
      const res = await rotateScimToken(tokenId);
      setNewScimToken(res.token);
      load();
      setMessage(res.message);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "No se pudo rotar el token.");
    }
  }

  async function onRevokeScimToken(tokenId: string) {
    setMessage(null);
    try {
      await revokeScimToken(tokenId);
      load();
      setMessage("Token revocado.");
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "No se pudo revocar el token.");
    }
  }

  async function onSaveScimMapping() {
    if (!scimGroup.trim()) return;
    setMessage(null);
    try {
      await upsertScimRoleMapping({ external_group: scimGroup.trim(), role_code: scimRole });
      setScimGroup("");
      load();
      setMessage("Mapeo grupo → rol guardado.");
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Mapeo no permitido.");
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
        <h2>Aprovisionamiento SCIM</h2>
        <p className="muted">
          SCIM permite que el proveedor de identidad de su organización cree, actualice y desactive usuarios automáticamente.
          Configure la URL base y un token Bearer para su IdP. Los grupos externos se mapean a roles internos mediante una lista permitida.
          Al desaprovisionar (<code>active=false</code>), el acceso se bloquea sin borrar el historial.
        </p>
        {scim && (
          <div className="form-stack">
            <label>
              <input
                type="checkbox"
                checked={scim.scim_enabled}
                onChange={(e) => onToggleScim(e.target.checked)}
              />
              {" "}Activar SCIM para esta organización
            </label>
            <p><strong>URL base SCIM:</strong> <code>{window.location.origin}{scim.scim_base_url}</code></p>
            <p className="muted">
              Usuarios activos: {scim.metrics.users_active ?? 0} · Desactivados: {scim.metrics.users_deactivated ?? 0} ·
              Conflictos pendientes: {scim.conflicts_pending}
            </p>
            {newScimToken && (
              <p role="status" className="panel">
                <strong>Token (cópielo ahora):</strong> <code>{newScimToken}</code>
              </p>
            )}
            <button type="button" onClick={onCreateScimToken}>Generar token</button>
            <table className="data-table">
              <thead><tr><th>Nombre</th><th>Prefijo</th><th>Estado</th><th>Último uso</th><th>Acciones</th></tr></thead>
              <tbody>
                {scim.tokens.map((t) => (
                  <tr key={t.id}>
                    <td>{t.name}</td>
                    <td>{t.masked}</td>
                    <td>{t.active ? "Activo" : "Inactivo"}</td>
                    <td>{t.last_used_at ? new Date(t.last_used_at).toLocaleString("es-CO") : "—"}</td>
                    <td className="button-row">
                      <button type="button" onClick={() => onRotateScimToken(t.id)}>Rotar</button>
                      <button type="button" onClick={() => onRevokeScimToken(t.id)}>Revocar</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <h3>Mapeo grupos → roles</h3>
            <div className="form-stack" style={{ marginBottom: "0.5rem" }}>
              <input placeholder="Grupo externo (displayName)" value={scimGroup} onChange={(e) => setScimGroup(e.target.value)} />
              <select value={scimRole} onChange={(e) => setScimRole(e.target.value)}>
                <option value="viewer">viewer</option>
                <option value="operator">operator</option>
              </select>
              <button type="button" onClick={onSaveScimMapping}>Guardar mapeo</button>
            </div>
            {scimMappings.length > 0 && (
              <ul>
                {scimMappings.map((m) => (
                  <li key={m.id}>{m.external_group} → {m.role_code}</li>
                ))}
              </ul>
            )}
            {scimConflicts.length > 0 && (
              <>
                <h3>Conflictos recientes</h3>
                <table className="data-table">
                  <thead><tr><th>Tipo</th><th>Detalle</th><th>Fecha</th></tr></thead>
                  <tbody>
                    {scimConflicts.map((c) => (
                      <tr key={c.id}>
                        <td>{c.conflict_type}</td>
                        <td className="cell-truncate">{c.detail || "—"}</td>
                        <td>{new Date(c.created_at).toLocaleString("es-CO")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </>
            )}
            {scim.recent_events.length > 0 && (
              <>
                <h3>Eventos SCIM recientes</h3>
                <table className="data-table">
                  <thead><tr><th>Acción</th><th>Resultado</th><th>Fecha</th></tr></thead>
                  <tbody>
                    {scim.recent_events.map((ev, i) => (
                      <tr key={`${ev.action}-${i}`}>
                        <td>{ev.action}</td>
                        <td>{ev.result}</td>
                        <td>{new Date(ev.created_at).toLocaleString("es-CO")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </>
            )}
          </div>
        )}
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
