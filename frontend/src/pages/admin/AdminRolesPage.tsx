import { useEffect, useState } from "react";
import { ApiError, fetchAdminRoles, fetchPermissionMatrix, type AdminRole } from "../../api";
import { EmptyState, ErrorState, LoadingState } from "../../components/AsyncState";

export function AdminRolesPage() {
  const [roles, setRoles] = useState<AdminRole[]>([]);
  const [matrix, setMatrix] = useState<Record<string, Record<string, boolean>>>({});
  const [permissions, setPermissions] = useState<Array<{ code: string; module: string }>>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([fetchAdminRoles(), fetchPermissionMatrix()])
      .then(([r, m]) => {
        setRoles(r);
        setMatrix(m.matrix);
        setPermissions(m.permissions);
      })
      .catch((e) => setError(e instanceof ApiError ? e.message : "Error al cargar roles"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingState message="Cargando roles…" />;
  if (error) return <ErrorState message={error} />;
  if (roles.length === 0) return <EmptyState title="Sin roles" />;

  const modules = [...new Set(permissions.map((p) => p.module))];

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Roles y permisos</h1>
        <p className="muted">Matriz de permisos por rol</p>
      </header>
      {modules.map((module) => (
        <section key={module} className="panel table-wrap">
          <h2>{module}</h2>
          <table className="data-table matrix-table">
            <thead>
              <tr>
                <th>Permiso</th>
                {roles.map((r) => <th key={r.id} title={r.code}>{r.name}</th>)}
              </tr>
            </thead>
            <tbody>
              {permissions.filter((p) => p.module === module).map((perm) => (
                <tr key={perm.code}>
                  <td className="mono">{perm.code}</td>
                  {roles.map((r) => (
                    <td key={r.id} className="matrix-cell">{matrix[r.id]?.[perm.code] ? "✓" : "—"}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ))}
      <p className="muted">Los roles de sistema no pueden modificarse desde V1. Roles personalizados: próxima iteración de edición en UI.</p>
    </div>
  );
}
