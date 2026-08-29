import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  ApiError,
  createAdminUser,
  fetchAdminRoles,
  fetchAdminUsersOverview,
  resetAdminUserPassword,
  setAdminUserStatus,
  type AdminRole,
  type AdminUserOverview,
} from "../../api";
import { EmptyState, ErrorState, LoadingState } from "../../components/AsyncState";
import { usePermissions } from "../../hooks/usePermissions";
import {
  IDENTITY_SOURCE_LABEL,
  PROVISION_STATUS_LABEL,
  USER_STATUS_LABEL,
  formatTs,
} from "./identityLabels";

const COLUMNAS = [
  { key: "username", label: "Usuario" },
  { key: "full_name", label: "Nombre" },
  { key: "email", label: "Correo" },
  { key: "organization_name", label: "Organización" },
  { key: "status", label: "Estado" },
  { key: "role", label: "Rol" },
  { key: "last_login_at", label: "Último acceso" },
  { key: "mfa", label: "MFA" },
  { key: "identity_origin", label: "Origen identidad" },
  { key: "provisioning", label: "Aprovisionamiento" },
  { key: "created_at", label: "Creación" },
  { key: "updated_at", label: "Actualización" },
] as const;

const COLS_KEY = "admin_users_cols_v1";

type SortKey = typeof COLUMNAS[number]["key"];
type SortDir = "asc" | "desc";

function loadVisibleCols(): Set<string> {
  try {
    const raw = localStorage.getItem(COLS_KEY);
    if (raw) return new Set(JSON.parse(raw) as string[]);
  } catch {
    /* ignore */
  }
  return new Set(["username", "full_name", "email", "organization_name", "status", "role", "last_login_at", "mfa", "identity_origin", "provisioning"]);
}

function mfaLabel(row: AdminUserOverview): string {
  if (row.mfa.enabled) return "Habilitado";
  if (row.mfa.enrollment_pending) return "Pendiente";
  if (row.mfa.mfa_required_by_policy) return "Requerido (no configurado)";
  return "No habilitado";
}

export function AdminUsersPage() {
  const { has } = usePermissions();
  const [users, setUsers] = useState<AdminUserOverview[]>([]);
  const [roles, setRoles] = useState<AdminRole[]>([]);
  const [q, setQ] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ username: "", password: "", email: "", full_name: "", role: "viewer" });
  const [tempPassword, setTempPassword] = useState<string | null>(null);
  const [visibleCols, setVisibleCols] = useState<Set<string>>(loadVisibleCols);
  const [sortKey, setSortKey] = useState<SortKey>("username");
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  useEffect(() => {
    localStorage.setItem(COLS_KEY, JSON.stringify([...visibleCols]));
  }, [visibleCols]);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    Promise.all([fetchAdminUsersOverview(q || undefined, statusFilter || undefined), fetchAdminRoles()])
      .then(([u, r]) => {
        setUsers(u);
        setRoles(r.filter((x) => x.is_active));
      })
      .catch((e) => setError(e instanceof ApiError ? e.message : "Error al cargar usuarios"))
      .finally(() => setLoading(false));
  }, [q, statusFilter]);

  useEffect(() => {
    load();
  }, [load]);

  const filtered = useMemo(() => {
    const rows = [...users].sort((a, b) => {
      const dir = sortDir === "asc" ? 1 : -1;
      const getVal = (row: AdminUserOverview): string => {
        switch (sortKey) {
          case "mfa":
            return mfaLabel(row);
          case "identity_origin":
            return row.identity_origin.source;
          case "provisioning":
            return row.provisioning.status;
          case "organization_name":
            return row.organization_name ?? "";
          default:
            return String((row as Record<string, unknown>)[sortKey] ?? "");
        }
      };
      return getVal(a).localeCompare(getVal(b), "es") * dir;
    });
    return rows;
  }, [users, sortKey, sortDir]);

  function toggleSort(key: SortKey) {
    if (sortKey === key) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortKey(key);
      setSortDir("asc");
    }
  }

  function toggleCol(key: string) {
    setVisibleCols((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    try {
      await createAdminUser(form);
      setShowForm(false);
      setForm({ username: "", password: "", email: "", full_name: "", role: "viewer" });
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo crear el usuario");
    }
  }

  if (loading) return <LoadingState message="Cargando usuarios…" />;
  if (error && users.length === 0) return <ErrorState message={error} onRetry={load} />;

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Usuarios</h1>
<<<<<<< HEAD
        <p className="muted">Administración de usuarios de la organización</p>
=======
        <p className="muted">Identidades del tenant: MFA, origen, aprovisionamiento y roles (1300/1370/1380)</p>
>>>>>>> b3046cc (feat(vistas): identidad, seguridad y accesos 1300/1370/1380 visible en UI)
      </header>

      <div className="ops-actions" style={{ flexWrap: "wrap", gap: "0.5rem" }}>
        {has("admin.user.create") && (
          <button type="button" className="btn primary" onClick={() => setShowForm((v) => !v)}>+ Crear usuario</button>
        )}
        <input placeholder="Buscar usuario, correo o nombre" value={q} onChange={(e) => setQ(e.target.value)} />
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">Todos los estados</option>
          {Object.entries(USER_STATUS_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <details>
          <summary className="btn">Columnas</summary>
          <div className="chip-row" style={{ marginTop: "0.5rem" }}>
            {COLUMNAS.map((c) => (
              <label key={c.key} className="chip">
                <input type="checkbox" checked={visibleCols.has(c.key)} onChange={() => toggleCol(c.key)} />
                {c.label}
              </label>
            ))}
          </div>
        </details>
      </div>

      {error && <p className="error">{error}</p>}
      {tempPassword && (
        <div className="panel warn">
          Contraseña temporal generada (cópiela ahora): <strong className="mono">{tempPassword}</strong>
          <button type="button" className="btn" onClick={() => setTempPassword(null)}>Cerrar</button>
        </div>
      )}

      {showForm && (
        <form className="panel" onSubmit={handleCreate}>
          <label>Usuario *<input required value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} /></label>
          <label>Contraseña *<input required type="password" minLength={8} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} /></label>
          <label>Email<input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></label>
          <label>Nombre completo<input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} /></label>
          <label>Rol *
            <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
              {roles.map((r) => <option key={r.id} value={r.code}>{r.name}</option>)}
            </select>
          </label>
          <div className="ops-actions">
            <button type="button" className="btn" onClick={() => setShowForm(false)}>Cancelar</button>
            <button type="submit" className="btn primary">Guardar</button>
          </div>
        </form>
      )}

      {filtered.length === 0 ? (
        <EmptyState title="Sin usuarios" message="No hay usuarios que coincidan con los filtros." />
      ) : (
        <div className="panel table-wrap">
          <table className="data-table compact">
            <thead>
              <tr>
                {COLUMNAS.filter((c) => visibleCols.has(c.key)).map((c) => (
                  <th key={c.key}>
                    <button type="button" className="linkish" onClick={() => toggleSort(c.key)}>
                      {c.label}{sortKey === c.key ? (sortDir === "asc" ? " ↑" : " ↓") : ""}
                    </button>
                  </th>
                ))}
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((u) => (
                <tr key={u.id}>
                  {visibleCols.has("username") && (
                    <td><Link to={`/administracion/usuarios/${u.id}`}>{u.username}</Link></td>
                  )}
                  {visibleCols.has("full_name") && <td>{u.full_name || "—"}</td>}
                  {visibleCols.has("email") && <td className="truncate">{u.email || "—"}</td>}
                  {visibleCols.has("organization_name") && <td>{u.organization_name || "—"}</td>}
                  {visibleCols.has("status") && (
                    <td><span className={`badge status-${u.status}`}>{USER_STATUS_LABEL[u.status] || u.status}</span></td>
                  )}
                  {visibleCols.has("role") && <td title={u.role}>{u.role_name || u.role}</td>}
                  {visibleCols.has("last_login_at") && <td className="mono-sm">{formatTs(u.last_login_at)}</td>}
                  {visibleCols.has("mfa") && (
                    <td title={`Método: ${u.mfa.allowed_method}`}>{mfaLabel(u)}</td>
                  )}
                  {visibleCols.has("identity_origin") && (
                    <td>
                      {IDENTITY_SOURCE_LABEL[u.identity_origin.source] || u.identity_origin.source}
                      {u.identity_origin.provider_name ? ` · ${u.identity_origin.provider_name}` : ""}
                    </td>
                  )}
                  {visibleCols.has("provisioning") && (
                    <td>{PROVISION_STATUS_LABEL[u.provisioning.status] || u.provisioning.status}</td>
                  )}
                  {visibleCols.has("created_at") && <td className="mono-sm">{formatTs(u.created_at)}</td>}
                  {visibleCols.has("updated_at") && <td className="mono-sm">{formatTs(u.updated_at)}</td>}
                  <td className="actions-cell">
                    <Link className="btn" to={`/administracion/usuarios/${u.id}`}>Detalle</Link>
                    {has("admin.user.activate") && u.status !== "ACTIVE" && (
                      <button type="button" className="btn" onClick={() => setAdminUserStatus(u.id, "ACTIVE").then(load)}>Activar</button>
                    )}
                    {has("admin.user.deactivate") && u.status === "ACTIVE" && (
                      <button type="button" className="btn" onClick={() => setAdminUserStatus(u.id, "INACTIVE").then(load)}>Desactivar</button>
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
                        Restablecer
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
