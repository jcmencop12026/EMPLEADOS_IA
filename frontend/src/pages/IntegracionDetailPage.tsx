import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import type { IntegrationConnector, IntegrationWiringDetail } from "../api";
import {
  executeIntegrationConnector,
  fetchIntegrationConnector,
  fetchIntegrationWiringDetail,
  testIntegrationConnector,
  updateIntegrationConnector,
} from "../api";
import { usePermissions } from "../hooks/usePermissions";
import {
  EVENT_HIGHLIGHT_TYPES,
  INTEGRATION_STATUS_LABELS,
  POLICY_DECISION_LABELS,
  formatTs,
  sanitizeDetail,
} from "./integrationLabels";

type Tab = "config" | "mapping" | "cableado" | "executions" | "health" | "eventos" | "auditoria";

export function IntegracionDetailPage() {
  const { connectorId } = useParams<{ connectorId: string }>();
  const { has } = usePermissions();
  const [tab, setTab] = useState<Tab>("cableado");
  const [connector, setConnector] = useState<IntegrationConnector | null>(null);
  const [wiring, setWiring] = useState<IntegrationWiringDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [configJson, setConfigJson] = useState("");
  const [mappingJson, setMappingJson] = useState("");
  const [schemaJson, setSchemaJson] = useState("");
  const [lastCorrelationId, setLastCorrelationId] = useState<string | null>(null);

  async function load() {
    if (!connectorId) return;
    const [c, w] = await Promise.all([
      fetchIntegrationConnector(connectorId),
      fetchIntegrationWiringDetail(connectorId),
    ]);
    setConnector(c);
    setWiring(w);
    setConfigJson(JSON.stringify(c.config ?? {}, null, 2));
    setMappingJson(JSON.stringify(c.mapping ?? [], null, 2));
    setSchemaJson(JSON.stringify(c.schema ?? {}, null, 2));
  }

  useEffect(() => {
    load().catch((e) => setError(e instanceof Error ? e.message : "Error al cargar"));
  }, [connectorId]);

  async function handleTest() {
    if (!connectorId || !has("integraciones.test")) return;
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
    if (!connectorId || !has("integraciones.execute")) return;
    setMessage(null);
    try {
      const res = await executeIntegrationConnector(connectorId, {});
      setLastCorrelationId(res.correlation_id ?? null);
      setMessage(
        `Ejecución ${res.status}: ${res.records_valid} válidos / ${res.records_processed} procesados`,
      );
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ejecución fallida");
    }
  }

  async function handleSave() {
    if (!connectorId || !has("integraciones.configure")) return;
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

  if (!connector || !wiring) {
    return (
      <div className="page">
        <p className="muted">Cargando conector…</p>
      </div>
    );
  }

  const corrLink =
    lastCorrelationId ||
    wiring.executions.find((e) => e.correlation_id)?.correlation_id ||
    null;

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>{connector.name}</h1>
          <p className="muted">
            {connector.code} · {INTEGRATION_STATUS_LABELS[connector.status] ?? connector.status} ·
            Credencial: {connector.secret_configured ? "Configurado" : "No configurado"}
            {connector.gov_catalog_entry_id && ` · Catálogo: ${connector.gov_catalog_entry_id}`}
          </p>
          {corrLink && (
            <p className="muted">
              correlation_id:{" "}
              <Link to={`/integraciones/trazabilidad?cid=${encodeURIComponent(corrLink)}`}>{corrLink}</Link>
            </p>
          )}
        </div>
        <div className="toolbar">
          <Link to="/integraciones" className="btn">Volver</Link>
          {has("integraciones.test") && (
            <button type="button" className="btn" onClick={() => void handleTest()}>Probar</button>
          )}
          {has("integraciones.execute") && (
            <button type="button" className="btn primary" onClick={() => void handleExecute()}>Ejecutar</button>
          )}
        </div>
      </header>

      {error && <div className="alert alert-error">{error}</div>}
      {message && <div className="alert alert-success">{message}</div>}

      <nav className="tab-nav">
        {(
          [
            ["cableado", "Cableado"],
            ["executions", "Ejecuciones"],
            ["eventos", "Eventos"],
            ["auditoria", "Auditoría"],
            ["health", "Salud"],
            ["config", "Configuración"],
            ["mapping", "Mapeo"],
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

      {tab === "cableado" && (
        <section className="card">
          <h2>Cableado gobierno / continuidad</h2>
          <div className="grid-2">
            <div>
              <h3>Catálogo gobierno</h3>
              {wiring.catalog_entry ? (
                <dl className="kv-list">
                  <dt>Nombre</dt><dd>{String(wiring.catalog_entry.name ?? "—")}</dd>
                  <dt>Estado</dt><dd>{String(wiring.catalog_entry.status ?? "—")}</dd>
                  <dt>Clasificación</dt><dd>{String(wiring.catalog_entry.classification_name ?? "—")}</dd>
                  <dt>Ambiente</dt><dd>{String(wiring.catalog_entry.data_environment ?? "—")}</dd>
                </dl>
              ) : (
                <p className="muted">Sin entrada de catálogo vinculada.</p>
              )}
              <h3>Política aplicable</h3>
              {wiring.policy ? (
                <dl className="kv-list">
                  <dt>Decisión</dt>
                  <dd>{POLICY_DECISION_LABELS[String(wiring.policy.provider_decision)] ?? String(wiring.policy.provider_decision)}</dd>
                  <dt>Restricciones</dt>
                  <dd>{(wiring.policy.restrictions as string[] | undefined)?.join("; ") || "—"}</dd>
                </dl>
              ) : (
                <p className="muted">Sin política resuelta.</p>
              )}
              <h3>Preflight (simulación)</h3>
              {wiring.preflight ? (
                <dl className="kv-list">
                  <dt>Decisión</dt><dd>{wiring.preflight.decision}</dd>
                  <dt>Permitido</dt><dd>{wiring.preflight.allowed ? "Sí" : "No"}</dd>
                  <dt>Motivos</dt><dd>{wiring.preflight.reasons.join("; ") || "—"}</dd>
                </dl>
              ) : (
                <p className="muted">Preflight no aplicable sin catálogo.</p>
              )}
            </div>
            <div>
              <h3>Continuidad</h3>
              <dl className="kv-list">
                <dt>Proveedor ref</dt><dd className="mono-sm">{wiring.continuidad.proveedor_ref}</dd>
                <dt>Servicio</dt><dd>{wiring.continuidad.servicio_nombre ?? "—"}</dd>
                <dt>Estado operacional</dt><dd>{wiring.continuidad.estado_operacional ?? "—"}</dd>
              </dl>
              <h3>Accesos gobierno (recientes)</h3>
              {wiring.access_logs.length === 0 ? (
                <p className="muted">Sin accesos registrados.</p>
              ) : (
                <table className="data-table compact">
                  <thead>
                    <tr><th>Acción</th><th>Resultado</th><th>Fecha</th></tr>
                  </thead>
                  <tbody>
                    {wiring.access_logs.slice(0, 8).map((a) => (
                      <tr key={String(a.id)}>
                        <td>{String(a.action)}</td>
                        <td>{String(a.result)}</td>
                        <td>{formatTs(String(a.created_at ?? ""))}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
              <h3>Linaje</h3>
              {wiring.lineage.length === 0 ? (
                <p className="muted">Sin eventos de linaje.</p>
              ) : (
                <ul>
                  {wiring.lineage.slice(0, 6).map((l) => (
                    <li key={String(l.id)}>{String(l.label)} — {String(l.step_type)}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </section>
      )}

      {tab === "config" && (
        <section className="card">
          <h2>Configuración (sin secretos)</h2>
          <textarea rows={14} value={configJson} onChange={(e) => setConfigJson(e.target.value)} disabled={!has("integraciones.configure")} />
          {has("integraciones.configure") && (
            <button type="button" className="btn primary" style={{ marginTop: "1rem" }} onClick={() => void handleSave()}>
              Guardar
            </button>
          )}
        </section>
      )}

      {tab === "mapping" && (
        <section className="card">
          <h2>Mapeo y esquema</h2>
          <label>
            Mapeo (JSON)
            <textarea rows={8} value={mappingJson} onChange={(e) => setMappingJson(e.target.value)} disabled={!has("integraciones.configure")} />
          </label>
          <label>
            Esquema esperado (JSON)
            <textarea rows={6} value={schemaJson} onChange={(e) => setSchemaJson(e.target.value)} disabled={!has("integraciones.configure")} />
          </label>
          {has("integraciones.configure") && (
            <button type="button" className="btn primary" onClick={() => void handleSave()}>Guardar mapeo</button>
          )}
        </section>
      )}

      {tab === "executions" && (
        <section className="card">
          <h2>Ejecuciones y resultados</h2>
          {wiring.executions.length === 0 ? (
            <p className="muted">Sin ejecuciones registradas.</p>
          ) : (
            <table className="data-table compact">
              <thead>
                <tr>
                  <th>Inicio</th>
                  <th>Estado</th>
                  <th>Válidos</th>
                  <th>Rechazados</th>
                  <th>Latencia</th>
                  <th>correlation_id</th>
                  <th>Error</th>
                </tr>
              </thead>
              <tbody>
                {wiring.executions.map((ex) => (
                  <tr key={ex.id}>
                    <td>{formatTs(ex.started_at)}</td>
                    <td>{ex.status}</td>
                    <td>{ex.records_valid}</td>
                    <td>{ex.records_rejected}</td>
                    <td>{ex.latency_ms != null ? `${ex.latency_ms} ms` : "—"}</td>
                    <td>
                      {ex.correlation_id ? (
                        <Link to={`/integraciones/trazabilidad?cid=${encodeURIComponent(ex.correlation_id)}`}>
                          {ex.correlation_id.slice(0, 8)}…
                        </Link>
                      ) : "—"}
                    </td>
                    <td>{ex.error_message ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}

      {tab === "health" && wiring.health && (
        <section className="card">
          <h2>Salud del conector</h2>
          <dl className="detail-grid">
            <dt>Estado</dt><dd>{INTEGRATION_STATUS_LABELS[wiring.health.status] ?? wiring.health.status}</dd>
            <dt>Circuit breaker</dt><dd>{wiring.health.circuit_open ? "Abierto" : "Cerrado"}</dd>
            <dt>Fallos consecutivos</dt><dd>{wiring.health.consecutive_failures}</dd>
            <dt>Último éxito</dt><dd>{formatTs(wiring.health.last_success_at)}</dd>
            <dt>Último error</dt><dd>{formatTs(wiring.health.last_error_at)}</dd>
            <dt>Tasa de éxito</dt><dd>{wiring.health.success_rate != null ? `${wiring.health.success_rate}%` : "—"}</dd>
          </dl>
        </section>
      )}

      {tab === "eventos" && (
        <section className="card">
          <h2>Eventos de continuidad</h2>
          {wiring.eventos.length === 0 ? (
            <p className="muted">Sin eventos vinculados.</p>
          ) : (
            <table className="data-table compact">
              <thead>
                <tr><th>Tipo</th><th>Severidad</th><th>Mensaje</th><th>Fecha</th></tr>
              </thead>
              <tbody>
                {wiring.eventos.map((ev) => (
                  <tr key={ev.id} className={EVENT_HIGHLIGHT_TYPES.includes(ev.tipo) ? "row-highlight" : ""}>
                    <td><strong>{ev.tipo}</strong></td>
                    <td>{ev.severidad}</td>
                    <td>{ev.mensaje}</td>
                    <td>{formatTs(ev.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}

      {tab === "auditoria" && (
        <section className="card">
          <h2>Auditoría</h2>
          {wiring.auditoria.length === 0 ? (
            <p className="muted">Sin entradas de auditoría para este conector.</p>
          ) : (
            <table className="data-table compact">
              <thead>
                <tr><th>Acción</th><th>Detalle</th><th>Fecha</th></tr>
              </thead>
              <tbody>
                {wiring.auditoria.map((a) => (
                  <tr key={a.id}>
                    <td>{a.action}</td>
                    <td className="truncate">{sanitizeDetail(a.detail)}</td>
                    <td>{formatTs(a.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}
    </div>
  );
}
