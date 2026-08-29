import { useCallback, useEffect, useState } from "react";
import {
  ApiError,
  fetchAdminSessions,
  fetchSecurityEvents,
  fetchSecurityPolicy,
  fetchSecuritySummary,
  revokeAdminSession,
  updateSecurityPolicy,
  type SecurityEvent,
  type SecurityPolicy,
  type SecuritySummary,
  type UserSession,
} from "../../api";
import { ErrorState, LoadingState } from "../../components/AsyncState";
import { formatAuditAction } from "../../lib/labels";

export function AdminSecurityPage() {
  const [summary, setSummary] = useState<SecuritySummary | null>(null);
  const [policy, setPolicy] = useState<SecurityPolicy | null>(null);
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [sessions, setSessions] = useState<UserSession[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([
      fetchSecuritySummary(),
      fetchSecurityPolicy().catch(() => null),
      fetchSecurityEvents(30).catch(() => []),
      fetchAdminSessions().catch(() => []),
    ])
      .then(([sum, pol, ev, sess]) => {
        setSummary(sum);
        setPolicy(pol);
        setEvents(ev);
        setSessions(sess);
        setError(null);
      })
      .catch((e) => setError(e instanceof ApiError ? e.message : "Error al cargar seguridad"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function onSavePolicy() {
    if (!policy) return;
    setMessage(null);
    try {
      const updated = await updateSecurityPolicy(policy);
      setPolicy(updated);
      setMessage("Política de seguridad actualizada.");
    } catch (e) {
      setMessage(e instanceof ApiError ? e.message : "No se pudo guardar la política.");
    }
  }

  if (loading) return <LoadingState message="Cargando panel de seguridad…" />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!summary) return null;

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Seguridad</h1>
        <p className="muted">Políticas, sesiones y eventos de la organización</p>
      </header>

      {message && <p className="panel" role="status">{message}</p>}

      <div className="dashboard-grid">
        <div className="panel dashboard-card"><span className="dashboard-card-value">{summary.users_active}</span><span className="dashboard-card-label">Usuarios activos</span></div>
        <div className="panel dashboard-card"><span className="dashboard-card-value">{summary.users_inactive}</span><span className="dashboard-card-label">Usuarios inactivos</span></div>
        <div className="panel dashboard-card"><span className="dashboard-card-value">{summary.users_blocked}</span><span className="dashboard-card-label">Usuarios bloqueados</span></div>
        <div className="panel dashboard-card"><span className="dashboard-card-value">{summary.roles_total}</span><span className="dashboard-card-label">Roles</span></div>
      </div>

      {policy && (
        <section className="panel">
          <h2>Política de seguridad</h2>
          <div className="form-stack">
            <label>
              Modo MFA
              <select
                value={policy.mfa_mode}
                onChange={(e) => setPolicy({ ...policy, mfa_mode: e.target.value })}
              >
                <option value="DESACTIVADO">Desactivado</option>
                <option value="OPCIONAL">Opcional</option>
                <option value="OBLIGATORIO">Obligatorio</option>
              </select>
            </label>
            <label>
              Duración de sesión (minutos)
              <input
                type="number"
                value={policy.session_duration_minutes}
                onChange={(e) => setPolicy({ ...policy, session_duration_minutes: Number(e.target.value) })}
              />
            </label>
            <label>
              Máximo de sesiones activas
              <input
                type="number"
                value={policy.max_active_sessions}
                onChange={(e) => setPolicy({ ...policy, max_active_sessions: Number(e.target.value) })}
              />
            </label>
            <label>
              Intentos de login antes de bloqueo
              <input
                type="number"
                value={policy.login_max_attempts}
                onChange={(e) => setPolicy({ ...policy, login_max_attempts: Number(e.target.value) })}
              />
            </label>
            <label>
              Minutos de bloqueo
              <input
                type="number"
                value={policy.lockout_minutes}
                onChange={(e) => setPolicy({ ...policy, lockout_minutes: Number(e.target.value) })}
              />
            </label>
            <button type="button" onClick={onSavePolicy}>Guardar política</button>
          </div>
        </section>
      )}

      <section className="panel">
        <h2>Sesiones activas</h2>
        <table className="data-table">
          <thead><tr><th>Usuario</th><th>IP</th><th>Última actividad</th><th></th></tr></thead>
          <tbody>
            {sessions.map((s) => (
              <tr key={s.id}>
                <td className="mono">{s.id.slice(0, 8)}…</td>
                <td>{s.ip_address || "—"}</td>
                <td>{new Date(s.last_activity_at).toLocaleString()}</td>
                <td>
                  <button type="button" onClick={() => revokeAdminSession(s.id).then(load)}>Revocar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="panel">
        <h2>Eventos de seguridad</h2>
        <table className="data-table">
          <thead><tr><th>Fecha</th><th>Tipo</th><th>Detalle</th></tr></thead>
          <tbody>
            {events.map((ev) => (
              <tr key={ev.id}>
                <td className="mono">{new Date(ev.created_at).toLocaleString()}</td>
                <td>{ev.event_type}</td>
                <td className="cell-truncate">{ev.detail || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="panel">
        <h2>Eventos administrativos recientes</h2>
        <table className="data-table">
          <thead><tr><th>Fecha</th><th>Acción</th><th>Detalle</th></tr></thead>
          <tbody>
            {summary.recent_events.map((ev, i) => (
              <tr key={`${ev.action}-${i}`}>
                <td className="mono">{new Date(ev.created_at).toLocaleString()}</td>
                  <td>{formatAuditAction(ev.action)}</td>
                <td className="cell-truncate">{ev.detail || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
