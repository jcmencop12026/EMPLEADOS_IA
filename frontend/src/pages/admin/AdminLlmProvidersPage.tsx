import { useCallback, useEffect, useState } from "react";
import {
  ApiError,
  createLlmProvider,
  createLlmRoutingPolicy,
  fetchLlmObservability,
  fetchLlmProviders,
  fetchLlmProvidersHealth,
  fetchLlmRoutingExplain,
  fetchLlmRoutingPolicies,
  testLlmProvider,
  updateLlmProvider,
  type LlmObservabilitySummary,
  type LlmProvider,
  type LlmProviderHealth,
  type LlmRoutingPolicy,
} from "../../api";
import { ErrorState, LoadingState } from "../../components/AsyncState";

const PROVIDER_OPTIONS = [
  { value: "openai", label: "OpenAI (operativo)" },
  { value: "ollama", label: "Ollama (opcional)" },
  { value: "anthropic", label: "Anthropic (preparado)" },
  { value: "gemini", label: "Gemini (preparado)" },
  { value: "azure-openai", label: "Azure OpenAI (preparado)" },
];

export function AdminLlmProvidersPage() {
  const [tab, setTab] = useState<"proveedores" | "salud" | "observabilidad" | "enrutamiento">("proveedores");
  const [providers, setProviders] = useState<LlmProvider[]>([]);
  const [health, setHealth] = useState<LlmProviderHealth[]>([]);
  const [observability, setObservability] = useState<LlmObservabilitySummary | null>(null);
  const [policies, setPolicies] = useState<LlmRoutingPolicy[]>([]);
  const [routingExplain, setRoutingExplain] = useState<string | null>(null);
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
    setError(null);
    Promise.all([
      fetchLlmProviders(),
      fetchLlmProvidersHealth(),
      fetchLlmObservability("7d"),
      fetchLlmRoutingPolicies(),
    ])
      .then(([p, h, o, pol]) => {
        setProviders(p);
        setHealth(h);
        setObservability(o);
        setPolicies(pol);
      })
      .catch((e) => setError(e instanceof ApiError ? e.message : "Error al cargar"))
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

  async function explainRouting() {
    try {
      const res = await fetchLlmRoutingExplain("openai");
      setRoutingExplain(res.razones.join(" · "));
    } catch {
      setRoutingExplain("No se pudo explicar el enrutamiento.");
    }
  }

  async function addDefaultPolicy() {
    try {
      await createLlmRoutingPolicy({
        name: "Preferir OpenAI",
        preferred_provider: "openai",
        fallback_allowed: true,
      });
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo crear política");
    }
  }

  if (loading) return <LoadingState message="Cargando proveedores IA…" />;
  if (error && providers.length === 0) return <ErrorState message={error} onRetry={load} />;

  return (
    <div className="ops-page">
      <header className="page-header compact">
        <h1>Proveedores de inferencia IA</h1>
        <p className="muted">Multiproveedor, enrutamiento, observabilidad y salud</p>
        <div className="toolbar compact-toolbar">
          {(["proveedores", "salud", "observabilidad", "enrutamiento"] as const).map((t) => (
            <button key={t} type="button" className={tab === t ? "btn primary small" : "btn small"} onClick={() => setTab(t)}>
              {t === "proveedores" ? "Proveedores" : t === "salud" ? "Salud" : t === "observabilidad" ? "Consumo" : "Enrutamiento"}
            </button>
          ))}
        </div>
      </header>

      {tab === "proveedores" && (
        <>
          <div className="ops-actions" style={{ marginBottom: "1rem" }}>
            <button type="button" className="btn primary" onClick={() => setShowForm(!showForm)}>
              {showForm ? "Cancelar" : "Nuevo proveedor"}
            </button>
          </div>
          {showForm && (
            <form className="panel compact-panel" onSubmit={handleCreate} style={{ marginBottom: "1rem" }}>
              <label>Nombre
                <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
              </label>
              <label>Tipo
                <select value={form.provider_type} onChange={(e) => setForm({ ...form, provider_type: e.target.value })}>
                  {PROVIDER_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </label>
              <label>Modelo por defecto
                <input value={form.model_default} onChange={(e) => setForm({ ...form, model_default: e.target.value })} />
              </label>
              <label>Endpoint (opcional)
                <input value={form.endpoint} onChange={(e) => setForm({ ...form, endpoint: e.target.value })} />
              </label>
              <label>Variable de entorno del secreto
                <input value={form.secret_env_var} onChange={(e) => setForm({ ...form, secret_env_var: e.target.value })} placeholder="OPENAI_API_KEY" />
              </label>
              <button type="submit" className="btn primary">Crear</button>
            </form>
          )}
          {testResult && <p className="muted">{testResult}</p>}
          <div className="panel compact-panel">
            <table className="data-table compact-table">
              <thead>
                <tr><th>Nombre</th><th>Tipo</th><th>Modelo</th><th>Estado salud</th><th>Secreto</th><th></th></tr>
              </thead>
              <tbody>
                {providers.map((p) => (
                  <tr key={p.id}>
                    <td>{p.name}{p.is_fallback ? " (fallback)" : ""}</td>
                    <td>{p.provider_label || p.provider_type}</td>
                    <td>{p.model_default || "—"}</td>
                    <td>{p.health_status || "—"}</td>
                    <td>{p.secret_configured ? p.secret_masked || "Configurado" : "No configurado"}</td>
                    <td className="ops-actions">
                      <button type="button" className="btn small" onClick={() => toggleEnabled(p)}>
                        {p.is_enabled ? "Deshabilitar" : "Habilitar"}
                      </button>
                      <button type="button" className="btn small" disabled={testingId === p.id} onClick={() => handleTest(p.id)}>
                        {testingId === p.id ? "Probando…" : "Probar"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === "salud" && (
        <div className="panel compact-panel">
          <table className="data-table compact-table">
            <thead><tr><th>Proveedor</th><th>Estado</th><th>Detalle</th><th>Modo</th></tr></thead>
            <tbody>
              {health.map((h) => (
                <tr key={h.provider_id}>
                  <td>{h.etiqueta}</td>
                  <td>{h.estado}</td>
                  <td>{h.detalle}</td>
                  <td>{h.modo || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === "observabilidad" && observability && (
        <div className="panel compact-panel">
          <dl className="detail-grid">
            <dt>Inferencias (periodo)</dt><dd>{observability.total_inferencias}</dd>
            <dt>Tasa de éxito</dt><dd>{observability.tasa_exito != null ? `${observability.tasa_exito}%` : "Sin información"}</dd>
            <dt>Latencia promedio</dt><dd>{observability.latencia_promedio_ms ?? "Sin información"}</dd>
            <dt>Tokens</dt><dd>{observability.tokens_total ?? "Sin información"}</dd>
            <dt>Costo</dt><dd>{observability.costo_total ?? "Sin información"}</dd>
            <dt>Fallbacks</dt><dd>{observability.fallbacks}</dd>
            <dt>Errores</dt><dd>{observability.errores}</dd>
          </dl>
        </div>
      )}

      {tab === "enrutamiento" && (
        <div className="panel compact-panel">
          <p><button type="button" className="btn small" onClick={explainRouting}>Explicar selección OpenAI</button></p>
          {routingExplain && <p className="muted">{routingExplain}</p>}
          <table className="data-table compact-table">
            <thead><tr><th>Política</th><th>Preferido</th><th>Modelo</th><th>Fallback</th><th>Activa</th></tr></thead>
            <tbody>
              {policies.map((p) => (
                <tr key={p.id}>
                  <td>{p.name}</td>
                  <td>{p.preferred_provider || "—"}</td>
                  <td>{p.preferred_model || "—"}</td>
                  <td>{p.fallback_allowed ? "Sí" : "No"}</td>
                  <td>{p.is_active ? "Sí" : "No"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p><button type="button" className="btn small" onClick={addDefaultPolicy}>Agregar política OpenAI</button></p>
        </div>
      )}

      {error && <p className="error">{error}</p>}
    </div>
  );
}
