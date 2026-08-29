import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import type { IntegrationConnector, IntegrationExecution, IntegrationHealth } from "../api";
import {
  executeIntegrationConnector,
  fetchIntegrationConnector,
  fetchIntegrationExecutions,
  fetchIntegrationHealth,
  testIntegrationConnector,
  updateIntegrationConnector,
} from "../api";

const STATUS_LABELS: Record<string, string> = {
  BORRADOR: "Borrador",
  CONFIGURANDO: "Configurando",
  VALIDANDO: "Validando",
  ACTIVO: "Activo",
  DEGRADADO: "Degradado",
  ERROR: "Error",
  INACTIVO: "Inactivo",
};

type Tab = "config" | "mapping" | "executions" | "health";

export function IntegracionDetailPage() {
  const { connectorId } = useParams<{ connectorId: string }>();
  const [tab, setTab] = useState<Tab>("config");
  const [connector, setConnector] = useState<IntegrationConnector | null>(null);
  const [executions, setExecutions] = useState<IntegrationExecution[]>([]);
  const [health, setHealth] = useState<IntegrationHealth | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [configJson, setConfigJson] = useState("");
  const [mappingJson, setMappingJson] = useState("");
  const [schemaJson, setSchemaJson] = useState("");

  async function load() {
    if (!connectorId) return;
    const [c, ex, h] = await Promise.all([
      fetchIntegrationConnector(connectorId),
      fetchIntegrationExecutions(connectorId),
      fetchIntegrationHealth(connectorId),
    ]);
    setConnector(c);
    setExecutions(ex);
    setHealth(h);
    setConfigJson(JSON.stringify(c.config ?? {}, null, 2));
    setMappingJson(JSON.stringify(c.mapping ?? [], null, 2));
    setSchemaJson(JSON.stringify(c.schema ?? {}, null, 2));
  }

  useEffect(() => {
    load().catch((e) => setError(e instanceof Error ? e.message : "Error al cargar"));
  }, [connectorId]);

  async function handleTest() {
    if (!connectorId) return;
    setMessage(null);
    try {
      const res = await testIntegrationConnector(connectorId);
      setMessage(`${res.resultado}: ${res.mensaje}`);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Prueba fallida");
    }
  }

  async function handleExecute() {
    if (!connectorId) return;
    setMessage(null);
    try {
      const res = await executeIntegrationConnector(connectorId, {});
      setMessage(
        `Ejecución ${res.status}: ${res.records_valid} válidos / ${res.records_processed} procesados`,
      );
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ejecución fallida");
    }
  }

  async function handleSave() {
    if (!connectorId) return;
    setError(null);
    try {
      await updateIntegrationConnector(connectorId, {
        config: JSON.parse(configJson),
        mapping: JSON.parse(mappingJson),
        schema: JSON.parse(schemaJson),
      });
      setMessage("Configuración guardada");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo guardar");
    }
  }

  if (!connector) {
    return (
      <div className="page">
        <p className="muted">Cargando conector…</p>
      </div>
    );
  }

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>{connector.name}</h1>
          <p className="muted">
            {connector.code} · {STATUS_LABELS[connector.status] ?? connector.status} · Credencial:{" "}
            {connector.secret_configured ? "Configurado" : "No configurado"}
          </p>
        </div>
        <div className="toolbar">
          <Link to="/integraciones" className="btn">
            Volver
          </Link>
          <button type="button" className="btn" onClick={() => void handleTest()}>
            Probar conexión
          </button>
          <button type="button" className="btn primary" onClick={() => void handleExecute()}>
            Ejecutar
          </button>
        </div>
      </header>

      {error && <div className="alert alert-error">{error}</div>}
      {message && <div className="alert alert-success">{message}</div>}

      <nav className="tab-nav">
        {(
          [
            ["config", "Configuración"],
            ["mapping", "Mapeo de datos"],
            ["executions", "Ejecuciones"],
            ["health", "Salud"],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            className={tab === id ? "tab active" : "tab"}
            onClick={() => setTab(id)}
          >
            {label}
          </button>
        ))}
      </nav>

      {tab === "config" && (
        <section className="card">
          <h2>Configuración</h2>
          <textarea rows={14} value={configJson} onChange={(e) => setConfigJson(e.target.value)} />
          <button type="button" className="btn primary" style={{ marginTop: "1rem" }} onClick={() => void handleSave()}>
            Guardar
          </button>
        </section>
      )}

      {tab === "mapping" && (
        <section className="card">
          <h2>Mapeo y esquema</h2>
          <label>
            Mapeo (JSON)
            <textarea rows={8} value={mappingJson} onChange={(e) => setMappingJson(e.target.value)} />
          </label>
          <label>
            Esquema esperado (JSON)
            <textarea rows={6} value={schemaJson} onChange={(e) => setSchemaJson(e.target.value)} />
          </label>
          <button type="button" className="btn primary" onClick={() => void handleSave()}>
            Guardar mapeo
          </button>
        </section>
      )}

      {tab === "executions" && (
        <section className="card">
          <h2>Ejecuciones</h2>
          {executions.length === 0 ? (
            <p className="muted">Sin ejecuciones registradas.</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Inicio</th>
                  <th>Estado</th>
                  <th>Procesados</th>
                  <th>Válidos</th>
                  <th>Rechazados</th>
                  <th>Latencia</th>
                  <th>Error</th>
                </tr>
              </thead>
              <tbody>
                {executions.map((ex) => (
                  <tr key={ex.id}>
                    <td>{ex.started_at ? new Date(ex.started_at).toLocaleString("es-CO") : "—"}</td>
                    <td>{ex.status}</td>
                    <td>{ex.records_processed}</td>
                    <td>{ex.records_valid}</td>
                    <td>{ex.records_rejected}</td>
                    <td>{ex.latency_ms != null ? `${ex.latency_ms} ms` : "—"}</td>
                    <td>{ex.error_message ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}

      {tab === "health" && health && (
        <section className="card">
          <h2>Salud del conector</h2>
          <dl className="detail-grid">
            <dt>Estado</dt>
            <dd>{STATUS_LABELS[health.status] ?? health.status}</dd>
            <dt>Circuit breaker</dt>
            <dd>{health.circuit_open ? "Abierto (degradado)" : "Cerrado"}</dd>
            <dt>Fallos consecutivos</dt>
            <dd>{health.consecutive_failures}</dd>
            <dt>Último éxito</dt>
            <dd>{health.last_success_at ? new Date(health.last_success_at).toLocaleString("es-CO") : "—"}</dd>
            <dt>Último error</dt>
            <dd>{health.last_error_at ? new Date(health.last_error_at).toLocaleString("es-CO") : "—"}</dd>
            <dt>Latencia última</dt>
            <dd>{health.last_latency_ms != null ? `${health.last_latency_ms} ms` : "—"}</dd>
            <dt>Tasa de éxito</dt>
            <dd>{health.success_rate != null ? `${health.success_rate}%` : "—"}</dd>
            <dt>Total ejecuciones</dt>
            <dd>{health.total_executions}</dd>
          </dl>
        </section>
      )}
    </div>
  );
}
