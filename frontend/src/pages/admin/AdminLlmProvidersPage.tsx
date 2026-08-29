import { useCallback, useEffect, useState } from "react";
import {
  ApiError,
  createLlmProvider,
  fetchLlmProviders,
  testLlmProvider,
  updateLlmProvider,
  type LlmProvider,
} from "../../api";
import { ErrorState, LoadingState } from "../../components/AsyncState";
import { SemanticBadge } from "../../components/SemanticBadge";

export function AdminLlmProvidersPage() {
  const [providers, setProviders] = useState<LlmProvider[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [testingId, setTestingId] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    name: "",
    provider_type: "openai",
    model_default: "gpt-4o-mini",
    endpoint: "",
    timeout_seconds: 60,
    priority: 100,
    is_enabled: true,
    is_fallback: false,
    secret_env_var: "OPENAI_API_KEY",
  });

  const load = useCallback(() => {
    setLoading(true);
    fetchLlmProviders()
      .then(setProviders)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Error al cargar proveedores"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleTest(id: string) {
    setTestingId(id);
    setTestResult(null);
    try {
      const res = await testLlmProvider(id);
      setTestResult(res.message);
    } catch (err) {
      setTestResult(err instanceof ApiError ? err.message : "Error de prueba");
    } finally {
      setTestingId(null);
    }
  }

  async function toggleEnabled(p: LlmProvider) {
    try {
      await updateLlmProvider(p.id, { is_enabled: !p.is_enabled });
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo actualizar");
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    try {
      await createLlmProvider({
        name: form.name,
        provider_type: form.provider_type,
        model_default: form.model_default || undefined,
        endpoint: form.endpoint || undefined,
        timeout_seconds: form.timeout_seconds,
        priority: form.priority,
        is_enabled: form.is_enabled,
        is_fallback: form.is_fallback,
        secret_env_var: form.secret_env_var || undefined,
      });
      setShowForm(false);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo crear");
    }
  }

  if (loading) return <LoadingState message="Cargando proveedores IA…" />;
  if (error && providers.length === 0) return <ErrorState message={error} onRetry={load} />;

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Proveedores de inferencia IA</h1>
        <p className="muted">Configuración de OpenAI, Ollama y futuros proveedores. Las salidas de inferencia se clasifican como <SemanticBadge tipo="INFERENCIA" />.</p>
      </header>

      <div className="ops-actions" style={{ marginBottom: "1rem" }}>
        <button type="button" className="btn primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Cancelar" : "Nuevo proveedor"}
        </button>
      </div>

      {showForm && (
        <form className="panel" onSubmit={handleCreate} style={{ marginBottom: "1rem" }}>
          <label>Nombre
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          </label>
          <label>Tipo
            <select value={form.provider_type} onChange={(e) => setForm({ ...form, provider_type: e.target.value })}>
              <option value="openai">OpenAI</option>
              <option value="ollama">Ollama</option>
            </select>
          </label>
          <label>Modelo por defecto
            <input value={form.model_default} onChange={(e) => setForm({ ...form, model_default: e.target.value })} />
          </label>
          <label>Endpoint (opcional)
            <input value={form.endpoint} onChange={(e) => setForm({ ...form, endpoint: e.target.value })} />
          </label>
          <label>Variable de entorno del secreto
            <input
              value={form.secret_env_var}
              onChange={(e) => setForm({ ...form, secret_env_var: e.target.value })}
              placeholder="OPENAI_API_KEY"
            />
          </label>
          <label>Prioridad
            <input
              type="number"
              value={form.priority}
              onChange={(e) => setForm({ ...form, priority: Number(e.target.value) })}
            />
          </label>
          <label>
            <input type="checkbox" checked={form.is_fallback} onChange={(e) => setForm({ ...form, is_fallback: e.target.checked })} />
            Usar como fallback
          </label>
          <button type="submit" className="btn primary">Crear</button>
        </form>
      )}

      {testResult && <p className="muted">{testResult}</p>}
      {error && <p className="error">{error}</p>}

      <div className="panel">
        <table className="data-table">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Tipo</th>
              <th>Modelo</th>
              <th>Prioridad</th>
              <th>Estado</th>
              <th>Secreto</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {providers.map((p) => (
              <tr key={p.id}>
                <td>{p.name}{p.is_fallback ? " (fallback)" : ""}</td>
                <td>{p.provider_type}</td>
                <td>{p.model_default || "—"}</td>
                <td>{p.priority}</td>
                <td>{p.is_enabled ? "Habilitado" : "Deshabilitado"}</td>
                <td>{p.secret_configured ? p.secret_masked || "Configurado" : "No configurado"}</td>
                <td className="ops-actions">
                  <button type="button" className="btn small" onClick={() => toggleEnabled(p)}>
                    {p.is_enabled ? "Deshabilitar" : "Habilitar"}
                  </button>
                  <button
                    type="button"
                    className="btn small"
                    disabled={testingId === p.id}
                    onClick={() => handleTest(p.id)}
                  >
                    {testingId === p.id ? "Probando…" : "Probar"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {providers.length === 0 && <p className="muted">No hay proveedores configurados.</p>}
      </div>
    </div>
  );
}
