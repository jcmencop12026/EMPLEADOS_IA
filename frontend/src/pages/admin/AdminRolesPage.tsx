import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ApiError,
  createAdminRole,
  fetchAdminRoles,
  fetchPermissionMatrix,
  updateRolePermissions,
  type AdminRole,
} from "../../api";
import { EmptyState, ErrorState, LoadingState } from "../../components/AsyncState";

function isEditableRole(role: AdminRole): boolean {
  return !role.is_system && role.organization_id !== null;
}

export function AdminRolesPage() {
  const [roles, setRoles] = useState<AdminRole[]>([]);
  const [matrix, setMatrix] = useState<Record<string, Record<string, boolean>>>({});
  const [permissions, setPermissions] = useState<Array<{ code: string; module: string; description: string | null }>>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [editingRoleId, setEditingRoleId] = useState<string | null>(null);
  const [draftCodes, setDraftCodes] = useState<Set<string>>(new Set());
  const [saving, setSaving] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [newRole, setNewRole] = useState({ code: "", name: "", description: "" });

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    Promise.all([fetchAdminRoles(), fetchPermissionMatrix()])
      .then(([r, m]) => {
        setRoles(r);
        setMatrix(m.matrix);
        setPermissions(m.permissions);
      })
      .catch((e) => setError(e instanceof ApiError ? e.message : "Error al cargar roles"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const modules = useMemo(() => [...new Set(permissions.map((p) => p.module))], [permissions]);
  const editingRole = roles.find((r) => r.id === editingRoleId) ?? null;

  function startEdit(role: AdminRole) {
    if (!isEditableRole(role)) return;
    const current = matrix[role.id] ?? {};
    setEditingRoleId(role.id);
    setDraftCodes(new Set(Object.entries(current).filter(([, v]) => v).map(([k]) => k)));
  }

  function cancelEdit() {
    setEditingRoleId(null);
    setDraftCodes(new Set());
  }

  function togglePermission(code: string) {
    setDraftCodes((prev) => {
      const next = new Set(prev);
      if (next.has(code)) next.delete(code);
      else next.add(code);
      return next;
    });
  }

  async function saveEdit() {
    if (!editingRoleId) return;
    setSaving(true);
    setError(null);
    try {
      await updateRolePermissions(editingRoleId, [...draftCodes]);
      setEditingRoleId(null);
      setDraftCodes(new Set());
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "No se pudieron guardar los permisos");
    } finally {
      setSaving(false);
    }
  }

  async function handleCreateRole(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await createAdminRole({
        code: newRole.code.trim(),
        name: newRole.name.trim(),
        description: newRole.description.trim() || null,
      });
      setShowCreate(false);
      setNewRole({ code: "", name: "", description: "" });
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "No se pudo crear el rol");
    }
  }

  if (loading) return <LoadingState message="Cargando roles…" />;
  if (error && roles.length === 0) return <ErrorState message={error} onRetry={load} />;
  if (roles.length === 0) return <EmptyState title="Sin roles" />;

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Roles y permisos</h1>
        <p className="muted">Matriz de permisos por rol. Los roles personalizados del tenant son editables.</p>
      </header>

      <div className="ops-actions">
        <button type="button" className="btn primary" onClick={() => setShowCreate((v) => !v)}>
          + Crear rol personalizado
        </button>
        {editingRole && (
          <>
            <span className="muted">Editando: <strong>{editingRole.name}</strong></span>
            <button type="button" className="btn primary" disabled={saving} onClick={saveEdit}>
              {saving ? "Guardando…" : "Guardar"}
            </button>
            <button type="button" className="btn" disabled={saving} onClick={cancelEdit}>
              Cancelar
            </button>
          </>
        )}
      </div>

      {error && <p className="error">{error}</p>}

      {showCreate && (
        <form className="panel form-grid" onSubmit={handleCreateRole}>
          <label>
            Código
            <input
              required
              pattern="[a-z0-9_]+"
              value={newRole.code}
              onChange={(e) => setNewRole((v) => ({ ...v, code: e.target.value }))}
              placeholder="ej. soporte_n1"
            />
          </label>
          <label>
            Nombre
            <input
              required
              value={newRole.name}
              onChange={(e) => setNewRole((v) => ({ ...v, name: e.target.value }))}
            />
          </label>
          <label>
            Descripción
            <input
              value={newRole.description}
              onChange={(e) => setNewRole((v) => ({ ...v, description: e.target.value }))}
            />
          </label>
          <div className="form-actions">
            <button type="submit" className="btn primary">Crear</button>
            <button type="button" className="btn" onClick={() => setShowCreate(false)}>Cerrar</button>
          </div>
        </form>
      )}

      {modules.map((module) => (
        <section key={module} className="panel table-wrap">
          <h2>{module}</h2>
          <table className="data-table matrix-table">
            <thead>
              <tr>
                <th>Permiso</th>
                {roles.map((r) => (
                  <th key={r.id} title={r.code}>
                    <div>{r.name}</div>
                    {isEditableRole(r) && editingRoleId !== r.id && (
                      <button type="button" className="btn link" onClick={() => startEdit(r)}>
                        Editar
                      </button>
                    )}
                    {isEditableRole(r) && editingRoleId === r.id && (
                      <span className="muted">(editando)</span>
                    )}
                    {!isEditableRole(r) && <span className="muted">solo lectura</span>}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {permissions.filter((p) => p.module === module).map((perm) => (
                <tr key={perm.code}>
                  <td className="mono" title={perm.description ?? undefined}>{perm.code}</td>
                  {roles.map((r) => {
                    const checked = editingRoleId === r.id
                      ? draftCodes.has(perm.code)
                      : Boolean(matrix[r.id]?.[perm.code]);
                    if (editingRoleId === r.id && isEditableRole(r)) {
                      return (
                        <td key={r.id} className="matrix-cell">
                          <input
                            type="checkbox"
                            checked={checked}
                            aria-label={`${perm.code} para ${r.name}`}
                            onChange={() => togglePermission(perm.code)}
                          />
                        </td>
                      );
                    }
                    return (
                      <td key={r.id} className="matrix-cell">{checked ? "✓" : "—"}</td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ))}
    </div>
  );
}
