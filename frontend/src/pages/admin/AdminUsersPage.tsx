import { useCallback, useEffect, useState } from "react";
import {
  ApiError,
  createAdminUser,
  fetchAdminRoles,
  fetchAdminUsers,
  resetAdminUserPassword,
  setAdminUserStatus,
  type AdminRole,
  type AdminUser,
} from "../../api";
import { EmptyState, ErrorState, LoadingState } from "../../components/AsyncState";

const STATUS_LABEL: Record<string, string> = {
  ACTIVE: "Activo",
  INACTIVE: "Inactivo",
  BLOCKED: "Bloqueado",
};

export function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [roles, setRoles] = useState<AdminRole[]>([]);
  const [q, setQ] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ username: "", password: "", email: "", full_name: "", role: "viewer" });
  const [tempPassword, setTempPassword] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    Promise.all([fetchAdminUsers(q || undefined, statusFilter || undefined), fetchAdminRoles()])
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
        <p className="muted">Administración de usuarios del tenant</p>
      </header>
      <div className="ops-actions">
        <button type="button" className="btn primary" onClick={() => setShowForm((v) => !v)}>+ Crear usuario</button>
        <input placeholder="Buscar" value={q} onChange={(e) => setQ(e.target.value)} />
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">Todos</option>
          {Object.entries(STATUS_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
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
      {users.length === 0 ? (
        <EmptyState title="Sin usuarios" message="No hay usuarios que coincidan con los filtros." />
      ) : (
        <div className="panel table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Usuario</th>
                <th>Nombre</th>
                <th>Email</th>
                <th>Rol</th>
                <th>Estado</th>
                <th>Último acceso</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>{u.username}</td>
                  <td>{u.full_name || "—"}</td>
                  <td>{u.email || "—"}</td>
                  <td>{u.role}</td>
                  <td><span className={`badge status-${u.status}`}>{STATUS_LABEL[u.status] || u.status}</span></td>
                  <td className="mono">{u.last_login_at ? new Date(u.last_login_at).toLocaleString() : "—"}</td>
                  <td className="actions-cell">
                    {u.status !== "ACTIVE" ? (
                      <button type="button" className="btn" title="Activar" onClick={() => setAdminUserStatus(u.id, "ACTIVE").then(load)}>Activar</button>
                    ) : (
                      <button type="button" className="btn" title="Desactivar" onClick={() => setAdminUserStatus(u.id, "INACTIVE").then(load)}>Desactivar</button>
                    )}
                    <button
                      type="button"
                      className="btn"
                      title="Restablecer contraseña"
                      onClick={async () => {
                        const res = await resetAdminUserPassword(u.id);
                        setTempPassword(res.temporary_password);
                      }}
                    >
                      Restablecer
                    </button>
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
