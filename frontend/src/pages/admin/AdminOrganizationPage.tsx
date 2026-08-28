import { useCallback, useEffect, useState } from "react";
import { ApiError, fetchAdminOrganization, updateAdminOrganization, type Organization } from "../../api";
import { EmptyState, ErrorState, LoadingState } from "../../components/AsyncState";

export function AdminOrganizationPage() {
  const [org, setOrg] = useState<Organization | null>(null);
  const [name, setName] = useState("");
  const [timezone, setTimezone] = useState("America/Bogota");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchAdminOrganization()
      .then((data) => {
        setOrg(data);
        setName(data.name);
        setTimezone(data.timezone || "America/Bogota");
      })
      .catch((e) => setError(e instanceof ApiError ? e.message : "Error al cargar la organización"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setSaved(false);
    try {
      const updated = await updateAdminOrganization({ name, timezone });
      setOrg(updated);
      setSaved(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo guardar");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <LoadingState message="Cargando organización…" />;
  if (error && !org) return <ErrorState message={error} onRetry={load} />;
  if (!org) return <EmptyState title="Sin datos" message="No se encontró información de la organización." />;

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Organización</h1>
        <p className="muted">Datos del tenant actual</p>
      </header>
      <form className="panel" onSubmit={save}>
        <table className="data-table">
          <tbody>
            <tr><th>Identificador</th><td className="mono">{org.slug || org.id}</td></tr>
            <tr><th>Estado</th><td>{org.status === "ACTIVE" ? "Activa" : org.status}</td></tr>
            <tr><th>Creada</th><td>{new Date(org.created_at).toLocaleString()}</td></tr>
          </tbody>
        </table>
        <label>Nombre *
          <input required value={name} onChange={(e) => setName(e.target.value)} />
        </label>
        <label>Zona horaria *
          <input required value={timezone} onChange={(e) => setTimezone(e.target.value)} placeholder="America/Bogota" />
        </label>
        {error && <p className="error">{error}</p>}
        {saved && <p className="muted">Cambios guardados correctamente.</p>}
        <div className="ops-actions">
          <button type="submit" className="btn primary" disabled={saving}>{saving ? "Guardando…" : "Guardar"}</button>
        </div>
      </form>
    </div>
  );
}
