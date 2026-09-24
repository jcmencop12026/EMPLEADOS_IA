import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ApiError,
  fetchAdminUserIdentityDetail,
  resetAdminUserPassword,
  setAdminUserStatus,
  type AdminUserIdentityDetail,
} from "../../api";
import { ErrorState, LoadingState } from "../../components/AsyncState";
import { usePermissions } from "../../hooks/usePermissions";
import { formatAuditAction } from "../../lib/labels";
import {
  IDENTITY_SOURCE_LABEL,
  MFA_MODE_LABEL,
  PROVISION_STATUS_LABEL,
  USER_STATUS_LABEL,
  formatTs,
  sanitizeAuditDetail,
} from "./identityLabels";

type Tab = "datos" | "roles" | "mfa" | "sesiones" | "aprovisionamiento" | "auditoria";

export function AdminUserDetailPage() {
  const { userId } = useParams<{ userId: string }>();
  const { has } = usePermissions();
  const [detail, setDetail] = useState<AdminUserIdentityDetail | null>(null);
  const [tab, setTab] = useState<Tab>("datos");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [tempPassword, setTempPassword] = useState<string | null>(null);

  useEffect(() => {
    if (!userId) return;
    setLoading(true);
    fetchAdminUserIdentityDetail(userId)
      .then((d) => {
        setDetail(d);
        setError(null);
      })
      .catch((e) => setError(e instanceof ApiError ? e.message : "No se pudo cargar el detalle"))
      .finally(() => setLoading(false));
  }, [userId]);

  if (loading) return <LoadingState message="Cargando identidad…" />;
  if (error || !detail) return <ErrorState message={error ?? "Usuario no encontrado"} />;

  const u = detail.user;

  return (
    <div className="ops-page">
      <header className="page-header">
        <div>
          <p className="muted"><Link to="/administracion/usuarios">← Usuarios</Link></p>
          <h1>{u.username}</h1>
          <p className="muted">
            {detail.organization_name} · {detail.role_name || u.role} · {USER_STATUS_LABEL[u.status] || u.status}
          </p>
        </div>
        <div className="toolbar">
          {has("admin.user.activate") && u.status !== "ACTIVE" && (
            <button type="button" className="btn" onClick={() => setAdminUserStatus(u.id, "ACTIVE").then(() => window.location.reload())}>
              Activar
            </button>
          )}
          {has("admin.user.deactivate") && u.status === "ACTIVE" && (
            <button type="button" className="btn" onClick={() => setAdminUserStatus(u.id, "INACTIVE").then(() => window.location.reload())}>
              Desactivar
            </button>
          )}
          {has("admin.user.reset_password") && (
            <button
              type="button"
              className="btn"
              onClick={async () => {
                const res = await resetAdminUserPassword(u.id);
                setTempPassword(res.temporary_password);
              }}
            >
              Restablecer contraseña
            </button>
          )}
        </div>
      </header>

      {tempPassword && (
        <div className="panel warn">
          Contraseña temporal (cópiela ahora): <strong className="mono">{tempPassword}</strong>
          <button type="button" className="btn" onClick={() => setTempPassword(null)}>Cerrar</button>
        </div>
      )}

      <nav className="tab-row">
        {(["datos", "roles", "mfa", "sesiones", "aprovisionamiento", "auditoria"] as Tab[]).map((t) => (
          <button key={t} type="button" className={tab === t ? "tab active" : "tab"} onClick={() => setTab(t)}>
            {t === "datos" ? "Datos" : t === "roles" ? "Roles y permisos" : t === "mfa" ? "MFA" : t === "sesiones" ? "Sesiones" : t === "aprovisionamiento" ? "Aprovisionamiento" : "Auditoría"}
          </button>
        ))}
      </nav>

      {tab === "datos" && (
        <section className="panel">
          <table className="data-table compact">
            <tbody>
              <tr><th>Usuario</th><td>{u.username}</td></tr>
              <tr><th>Nombre</th><td>{u.full_name || "—"}</td></tr>
              <tr><th>Correo</th><td>{u.email || "—"}</td></tr>
              <tr><th>Organización</th><td>{detail.organization_name || u.organization_id}</td></tr>
              <tr><th>Rol</th><td>{detail.role_name || u.role} <span className="muted mono-sm">({u.role})</span></td></tr>
              <tr><th>Estado</th><td>{USER_STATUS_LABEL[u.status] || u.status}</td></tr>
              <tr><th>Último acceso</th><td className="mono-sm">{formatTs(u.last_login_at)}</td></tr>
              <tr><th>Origen identidad</th>
                <td>
                  {IDENTITY_SOURCE_LABEL[detail.identity_origin.source] || detail.identity_origin.source}
                  {detail.identity_origin.provider_name ? ` — ${detail.identity_origin.provider_name}` : ""}
                  {detail.identity_origin.external_subject_ref ? ` (${detail.identity_origin.external_subject_ref})` : ""}
                </td>
              </tr>
              <tr><th>Creación</th><td className="mono-sm">{formatTs(u.created_at)}</td></tr>
              <tr><th>Actualización</th><td className="mono-sm">{formatTs(u.updated_at)}</td></tr>
            </tbody>
          </table>
        </section>
      )}

      {tab === "roles" && (
        <section className="panel">
          <h2>Rol asignado</h2>
          <p><strong>{detail.role_name || u.role}</strong> <span className="muted mono-sm">{u.role}</span></p>
          <p className="muted">Organización: {detail.organization_name} (solo permisos de esta organización)</p>
          <h3>Permisos efectivos ({detail.permissions_effective.length})</h3>
          <p className="muted">Origen: rol autoritativo en la organización actual.</p>
          <div className="chip-row">
            {detail.permissions_effective.map((p) => (
              <span key={p.code} className="chip" title={`${p.source} · ${p.role_code ?? ""}`}>{p.code}</span>
            ))}
          </div>
          {detail.permissions_effective.length === 0 && <p className="muted">Sin permisos efectivos (deny by default).</p>}
        </section>
      )}

      {tab === "mfa" && (
        <section className="panel">
          <table className="data-table compact">
            <tbody>
              <tr><th>Estado MFA</th><td>{detail.mfa.enabled ? "Habilitado" : detail.mfa.enrollment_pending ? "Configuración pendiente" : "No habilitado"}</td></tr>
              <tr><th>Método permitido</th><td>{detail.mfa.allowed_method}</td></tr>
              <tr><th>Política org.</th><td>{MFA_MODE_LABEL[detail.mfa.policy_mfa_mode ?? ""] || detail.mfa.policy_mfa_mode || "—"}</td></tr>
              <tr><th>Requerido por política</th><td>{detail.mfa.mfa_required_by_policy ? "Sí" : "No"}</td></tr>
              <tr><th>Confirmado</th><td className="mono-sm">{formatTs(detail.mfa.confirmed_at)}</td></tr>
              <tr><th>Último cambio MFA</th><td className="mono-sm">{formatTs(detail.mfa.updated_at)}</td></tr>
            </tbody>
          </table>
          <p className="muted" style={{ marginTop: "1rem" }}>
            No se muestran semillas TOTP, tokens ni códigos de recuperación. Gestión self-service en Mi seguridad según permisos del usuario.
          </p>
        </section>
      )}

      {tab === "sesiones" && (
        <section className="panel">
          {detail.sessions.length === 0 ? (
            <p className="muted">Sin sesiones activas registradas.</p>
          ) : (
            <table className="data-table compact">
              <thead>
                <tr><th>Inicio</th><th>Última actividad</th><th>IP</th><th>Método</th><th>MFA sesión</th></tr>
              </thead>
              <tbody>
                {detail.sessions.map((s) => (
                  <tr key={s.id}>
                    <td className="mono-sm">{formatTs(s.created_at)}</td>
                    <td className="mono-sm">{formatTs(s.last_activity_at)}</td>
                    <td>{s.ip_address || "—"}</td>
                    <td>{s.auth_method || "—"}</td>
                    <td>{s.mfa_verified ? "Verificado" : "No"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}

      {tab === "aprovisionamiento" && (
        <section className="panel">
          <table className="data-table compact">
            <tbody>
              <tr><th>Estado</th><td>{PROVISION_STATUS_LABEL[detail.provisioning.status] || detail.provisioning.status}</td></tr>
              <tr><th>ID externo</th><td className="mono-sm">{detail.provisioning.external_id || "—"}</td></tr>
              <tr><th>Recurso SCIM</th><td className="mono-sm">{detail.provisioning.scim_resource_id || "—"}</td></tr>
              <tr><th>Última actualización</th><td className="mono-sm">{formatTs(detail.provisioning.updated_at)}</td></tr>
            </tbody>
          </table>
          {detail.scim_user_events.length > 0 && (
            <>
              <h3>Eventos SCIM del usuario</h3>
              <table className="data-table compact">
                <thead><tr><th>Fecha</th><th>Acción</th><th>Resultado</th><th>Detalle</th><th>Correlación</th></tr></thead>
                <tbody>
                  {detail.scim_user_events.map((ev, i) => (
                    <tr key={i}>
                      <td className="mono-sm">{formatTs(ev.created_at)}</td>
                      <td>{ev.action}</td>
                      <td>{ev.result}</td>
                      <td className="truncate">{sanitizeAuditDetail(ev.detail)}</td>
                      <td className="mono-sm">{ev.correlation_id || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
          {detail.provisioning.status === "MANUAL" && (
            <p className="muted">Usuario no vinculado a recurso SCIM; creado o gestionado manualmente en la organización.</p>
          )}
        </section>
      )}

      {tab === "auditoria" && (
        <section className="panel">
          {detail.audit_entries.length === 0 ? (
            <p className="muted">Sin eventos de auditoría relacionados.</p>
          ) : (
            <table className="data-table compact">
              <thead>
                <tr><th>Fecha</th><th>Flujo</th><th>Acción</th><th>Resultado</th><th>Actor</th><th>Detalle</th><th>Correlación</th></tr>
              </thead>
              <tbody>
                {detail.audit_entries.map((ev, i) => (
                  <tr key={i}>
                    <td className="mono-sm">{formatTs(ev.created_at)}</td>
                    <td>{ev.stream}</td>
                    <td>{ev.stream === "auditoria" ? formatAuditAction(ev.action) : ev.action}</td>
                    <td>{ev.result || "—"}</td>
                    <td className="mono-sm truncate">{ev.actor_id ? ev.actor_id.slice(0, 8) + "…" : "—"}</td>
                    <td className="truncate">{sanitizeAuditDetail(ev.detail)}</td>
                    <td className="mono-sm">{ev.correlation_id || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}
    </div>
  );
}
