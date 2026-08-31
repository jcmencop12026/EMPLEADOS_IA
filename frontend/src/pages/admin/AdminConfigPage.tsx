import { useCallback, useEffect, useState } from "react";
import { ApiError, fetchOrgConfig, updateOrgConfig, type OrgConfig } from "../../api";
import { ErrorState, LoadingState } from "../../components/AsyncState";

export function AdminConfigPage() {
  const [config, setConfig] = useState<OrgConfig | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    fetchOrgConfig()
      .then(setConfig)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Error al cargar configuración"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (!config) return;
    setSaving(true);
    try {
      const updated = await updateOrgConfig(config);
      setConfig(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo guardar");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <LoadingState message="Cargando configuración…" />;
  if (error && !config) return <ErrorState message={error} onRetry={load} />;
  if (!config) return null;

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Configuración</h1>
        <p className="muted">Parámetros empresariales de la organización</p>
      </header>
      <form className="panel" onSubmit={save}>
        <label>Idioma por defecto
          <select value={config.language} onChange={(e) => setConfig({ ...config, language: e.target.value })}>
            <option value="es">Español</option>
          </select>
        </label>
        <label>Zona horaria
          <input value={config.timezone} onChange={(e) => setConfig({ ...config, timezone: e.target.value })} />
        </label>
        <label>Formato de fecha
          <select value={config.date_format} onChange={(e) => setConfig({ ...config, date_format: e.target.value })}>
            <option value="DD/MM/YYYY">DD/MM/YYYY</option>
            <option value="YYYY-MM-DD">YYYY-MM-DD</option>
          </select>
        </label>
        <label>Formato de hora
          <select value={config.time_format} onChange={(e) => setConfig({ ...config, time_format: e.target.value })}>
            <option value="24h">24 horas</option>
            <option value="12h">12 horas</option>
          </select>
        </label>
        {error && <p className="error">{error}</p>}
        <div className="ops-actions">
          <button type="submit" className="btn primary" disabled={saving}>{saving ? "Guardando…" : "Guardar"}</button>
        </div>
      </form>
    </div>
  );
}
