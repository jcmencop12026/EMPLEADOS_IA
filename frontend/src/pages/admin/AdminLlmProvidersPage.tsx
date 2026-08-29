import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ApiError,
  createLlmProvider,
  createLlmRoutingPolicy,
  fetchLlmInferenceLogs,
  fetchLlmModels,
  fetchLlmObservability,
  fetchLlmProviders,
  fetchLlmProvidersHealth,
  fetchLlmRoutingExplain,
  fetchLlmRoutingPolicies,
  testLlmProvider,
  updateLlmProvider,
  type LlmInferenceLog,
  type LlmModelCatalog,
  type LlmObservabilitySummary,
  type LlmProvider,
  type LlmProviderHealth,
  type LlmRoutingPolicy,
} from "../../api";
import { ErrorState, LoadingState } from "../../components/AsyncState";
import { HelpTooltip } from "../../components/optimizacion/HelpTooltip";
import { TOOLTIPS } from "../../lib/optimizacionLabels";
import { getCachedUser } from "../../auth/session";

const PROVIDER_OPTIONS = [
  { value: "openai", label: "OpenAI (operativo)" },
  { value: "ollama", label: "Ollama (compatibilidad opcional)" },
  { value: "anthropic", label: "Anthropic (preparado)" },
  { value: "gemini", label: "Gemini (preparado)" },
  { value: "azure-openai", label: "Azure OpenAI (preparado)" },
];

type Tab = "proveedores" | "modelos" | "salud" | "observabilidad" | "logs" | "enrutamiento";

export function AdminLlmProvidersPage() {
  const user = getCachedUser();
  const canManage = user?.permissions?.includes("llm.manage");
  const canFinops = user?.permissions?.includes("finops.view");
  const [tab, setTab] = useState<Tab>("proveedores");
  const [providers, setProviders] = useState<LlmProvider[]>([]);
  const [models, setModels] = useState<LlmModelCatalog[]>([]);
  const [health, setHealth] = useState<LlmProviderHealth[]>([]);
  const [observability, setObservability] = useState<LlmObservabilitySummary | null>(null);
  const [logs, setLogs] = useState<LlmInferenceLog[]>([]);
  const [policies, setPolicies] = useState<LlmRoutingPolicy[]>([]);
  const [routingExplain, setRoutingExplain] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [testingId, setTestingId] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [periodo, setPeriodo] = useState("7d");
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
      fetchLlmModels(),
      fetchLlmProvidersHealth(),
      fetchLlmObservability(periodo),
      fetchLlmInferenceLogs(50),
      fetchLlmRoutingPolicies(),
    ])
      .then(([p, m, h, o, l, pol]) => {
        setProviders(p);
        setModels(m);
        setHealth(h);
        setObservability(o);
        setLogs(l);
        setPolicies(pol);
      })
      .catch((e) => setError(e instanceof ApiError ? e.message : "Error al cargar"))
      .finally(() => setLoading(false));
  }, [periodo]);

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
    if (!canManage) return;
    try {
      await updateLlmProvider(p.id, { is_enabled: !p.is_enabled });
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo actualizar");
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!canManage) return;
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
      setRoutingExplain(res.seleccionado ?? { razones: res.razones });
    } catch {
      setRoutingExplain({ error: "No se pudo explicar el enrutamiento." });
    }
  }

  async function addDefaultPolicy() {
    if (!canManage) return;
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
        <h1>Multiproveedor IA</h1>
        <p className="muted">
          Proveedores, modelos, enrutamiento y observabilidad.
          <HelpTooltip text={TOOLTIPS.observabilidad} />
        </p>
        <div className="toolbar compact-tabs">
          {(["proveedores", "modelos", "salud", "observabilidad", "logs", "enrutamiento"] as const).map((t) => (
            <button key={t} type="button" className={tab === t ? "btn primary small" : "btn small"} onClick={() => setTab(t)}>
              {t === "proveedores" ? "Proveedores" : t === "modelos" ? "Modelos" : t === "salud" ? "Salud" : t === "observabilidad" ? "Consumo" : t === "logs" ? "Solicitudes" : "Enrutamiento"}
            </button>
          ))}
        </div>
      </header>

      {tab === "proveedores" && (
        <>
          {canManage && (
            <div className="ops-actions" style={{ marginBottom: "1rem" }}>
              <button type="button" className="btn primary" onClick={() => setShowForm(!showForm)}>
                {showForm ? "Cancelar" : "Nuevo proveedor"}
              </button>
            </div>
          )}
          {showForm && canManage && (
            <form className="panel compact-panel" onSubmit={handleCreate} style={{ marginBottom: "1rem" }}>
              <label>Nombre<input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required /></label>
              <label>Tipo
                <select value={form.provider_type} onChange={(e) => setForm({ ...form, provider_type: e.target.value })}>
                  {PROVIDER_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </label>
              <label>Modelo por defecto<input value={form.model_default} onChange={(e) => setForm({ ...form, model_default: e.target.value })} /></label>
              <label>Variable de entorno del secreto (no se almacena el valor)
                <input value={form.secret_env_var} onChange={(e) => setForm({ ...form, secret_env_var: e.target.value })} placeholder="OPENAI_API_KEY" />
              </label>
              <button type="submit" className="btn primary">Crear</button>
            </form>
          )}
          {testResult && <p className="muted">{testResult}</p>}
          <div className="panel compact-panel">
            <table className="data-table compact-table">
              <thead><tr><th>Nombre</th><th>Tipo</th><th>Modelo</th><th>Prioridad</th><th>Salud</th><th>Credencial</th><th></th></tr></thead>
              <tbody>
                {providers.map((p) => (
                  <tr key={p.id}>
                    <td>{p.name}{p.is_fallback ? " (fallback)" : ""}</td>
                    <td>{p.provider_label || p.provider_type}</td>
                    <td>{p.model_default || "—"}</td>
                    <td>{p.priority}</td>
                    <td>{p.health_status || "—"}</td>
                    <td>{p.secret_configured ? (p.secret_masked || "Configurado") : "No configurado"}</td>
                    <td className="ops-actions">
                      {canManage && (
                        <button type="button" className="btn small" onClick={() => toggleEnabled(p)}>
                          {p.is_enabled ? "Deshabilitar" : "Habilitar"}
                        </button>
                      )}
                      {canManage && (
                        <button type="button" className="btn small" disabled={testingId === p.id} onClick={() => handleTest(p.id)}>
                          {testingId === p.id ? "Probando…" : "Probar"}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === "modelos" && (
        <div className="panel compact-panel">
          <table className="data-table compact-table">
            <thead><tr><th>Modelo</th><th>Proveedor</th><th>Estado</th><th>Prioridad</th><th>Contexto</th><th>Habilitado</th></tr></thead>
            <tbody>
              {models.length === 0 ? (
                <tr><td colSpan={6} className="muted">Sin modelos en catálogo.</td></tr>
              ) : models.map((m) => (
                <tr key={m.id}>
                  <td>{m.display_name}</td>
                  <td>{m.provider_type}</td>
                  <td>{m.estado}</td>
                  <td>{m.priority}</td>
                  <td>{m.context_window ?? "—"}</td>
                  <td>{m.is_enabled ? "Sí" : "No"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === "salud" && (
        <div className="panel compact-panel">
          <table className="data-table compact-table">
            <thead><tr><th>Proveedor</th><th>Estado</th><th>Detalle</th><th>Modo</th><th>Latencia</th><th>Prioridad</th></tr></thead>
            <tbody>
              {health.map((h) => (
                <tr key={h.provider_id}>
                  <td>{h.etiqueta}</td>
                  <td>{h.estado}</td>
                  <td>{h.detalle}</td>
                  <td>{h.modo || "—"}</td>
                  <td>{h.latencia_ms != null ? `${h.latencia_ms} ms` : "—"}</td>
                  <td>{h.prioridad}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === "observabilidad" && observability && (
        <div className="panel compact-panel">
          <div style={{ marginBottom: 8 }}>
            <select value={periodo} onChange={(e) => setPeriodo(e.target.value)}>
              <option value="mtd">Mes actual</option>
              <option value="7d">7 días</option>
              <option value="30d">30 días</option>
            </select>
            {canFinops && <Link to="/costos-valor" style={{ marginLeft: 12 }}>Ver FinOps detallado →</Link>}
          </div>
          <div className="compact-metrics">
            <div><span className="muted">Solicitudes</span><strong>{observability.total_inferencias}</strong></div>
            <div><span className="muted">Éxitos</span><strong>{observability.exitosas}</strong></div>
            <div><span className="muted">Fallos</span><strong>{observability.errores}</strong></div>
            <div><span className="muted">Tasa éxito</span><strong>{observability.tasa_exito != null ? `${observability.tasa_exito}%` : "—"}</strong></div>
            <div><span className="muted">Latencia prom.</span><strong>{observability.latencia_promedio_ms ?? "—"} ms</strong></div>
            <div><span className="muted">Tokens</span><strong>{observability.tokens_total ?? "—"}</strong></div>
            {canFinops && (
              <div><span className="muted">Costo<HelpTooltip text={TOOLTIPS.finops} /></span><strong>{observability.costo_total ?? "—"}</strong></div>
            )}
            <div><span className="muted">Fallbacks</span><strong>{observability.fallbacks}</strong></div>
          </div>
          {Object.keys(observability.por_proveedor ?? {}).length > 0 && (
            <table className="data-table compact-table" style={{ marginTop: 8 }}>
              <thead><tr><th>Proveedor</th><th>Uso</th></tr></thead>
              <tbody>
                {Object.entries(observability.por_proveedor).map(([k, v]) => (
                  <tr key={k}><td>{k}</td><td>{v}</td></tr>
                ))}
              </tbody>
            </table>
          )}
          {Object.keys(observability.errores_por_categoria ?? {}).length > 0 && (
            <table className="data-table compact-table" style={{ marginTop: 8 }}>
              <thead><tr><th>Error normalizado</th><th>Cantidad</th></tr></thead>
              <tbody>
                {Object.entries(observability.errores_por_categoria).map(([k, v]) => (
                  <tr key={k}><td>{k}</td><td>{v}</td></tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {tab === "logs" && (
        <div className="panel compact-panel">
          <table className="data-table compact-table">
            <thead>
              <tr><th>Fecha</th><th>Trace</th><th>Proveedor</th><th>Modelo</th><th>Estado</th><th>Tokens</th><th>Latencia</th>{canFinops && <th>Costo</th>}<th>Fallback</th></tr>
            </thead>
            <tbody>
              {logs.length === 0 ? (
                <tr><td colSpan={canFinops ? 9 : 8} className="muted">Sin solicitudes registradas.</td></tr>
              ) : logs.map((l) => (
                <tr key={l.id}>
                  <td>{l.created_at ? new Date(l.created_at).toLocaleString("es-CO") : "—"}</td>
                  <td className="mono">{l.trace_id.slice(0, 10)}…</td>
                  <td>{l.provider ?? "—"}</td>
                  <td>{l.model ?? "—"}</td>
                  <td>{l.status}</td>
                  <td>{l.tokens_total ?? "—"}</td>
                  <td>{l.latency_ms ?? "—"} ms</td>
                  {canFinops && <td>{l.cost ?? "—"}</td>}
                  <td>{l.fallback_used ? "Sí" : "No"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === "enrutamiento" && (
        <div className="panel compact-panel">
          <p>
            <button type="button" className="btn small" onClick={explainRouting}>Explicar selección OpenAI</button>
            <HelpTooltip text={TOOLTIPS.routing} />
          </p>
          {routingExplain && <pre className="compact-pre">{JSON.stringify(routingExplain, null, 2)}</pre>}
          <table className="data-table compact-table">
            <thead><tr><th>Política</th><th>Preferido</th><th>Modelo</th><th>Fallback</th><th>Prioridad</th><th>Activa</th></tr></thead>
            <tbody>
              {policies.map((p) => (
                <tr key={p.id}>
                  <td>{p.name}</td>
                  <td>{p.preferred_provider || "—"}</td>
                  <td>{p.preferred_model || "—"}</td>
                  <td>{p.fallback_allowed ? "Sí" : "No"}</td>
                  <td>{p.priority}</td>
                  <td>{p.is_active ? "Sí" : "No"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {canManage && <p><button type="button" className="btn small" onClick={addDefaultPolicy}>Agregar política OpenAI</button></p>}
        </div>
      )}

      {error && <p className="error">{error}</p>}
    </div>
  );
}
