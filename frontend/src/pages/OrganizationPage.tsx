import { useCallback, useEffect, useState } from "react";
import { ApiError, fetchOrganization, type Organization } from "../api";
import { EmptyState, ErrorState, LoadingState } from "../components/AsyncState";

export function OrganizationPage() {
  const [org, setOrg] = useState<Organization | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchOrganization()
      .then(setOrg)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Error al cargar la organización."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) return <LoadingState message="Cargando organización…" />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!org) return <EmptyState title="Sin datos" message="No se encontró información de la organización." />;

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Organización</h1>
        <p className="muted">Datos de la organización actual</p>
      </header>
      <div className="panel">
        <table className="data-table">
          <tbody>
            <tr>
              <th>Nombre</th>
              <td>{org.name}</td>
            </tr>
            <tr>
              <th>Identificador</th>
              <td className="mono">{org.id}</td>
            </tr>
            <tr>
              <th>Creada</th>
              <td>{new Date(org.created_at).toLocaleString()}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
