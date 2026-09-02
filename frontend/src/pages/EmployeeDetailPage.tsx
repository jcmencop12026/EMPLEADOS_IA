import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import {
  activateEmployee,
  ApiError,
  assignEmployeeCapability,
  assignEmployeeKnowledge,
  assignEmployeeTool,
  certifyEmployee,
  decideEmployeeApproval,
  ejecutarMejoraFabrica,
  fetchEmployeeApprovals,
  fetchEmployeeCapabilities,
  fetchEmployeeDetail,
  fetchEmployeeHealth,
  fetchEmployeeInventory,
  fetchEmployeeKnowledge,
  fetchEmployeeTools,
  fetchEmployeeVersions,
  fetchMejoraTrazabilidad,
  iniciarMejoraAuditor,
  publishEmployee,
  reauditarMejora,
  removeEmployeeCapability,
  removeEmployeeKnowledge,
  removeEmployeeTool,
  requestEmployeeApproval,
  retireEmployee,
  rollbackEmployee,
  testEmployee,
  trainEmployee,
  validateEmployee,
  type CatalogItem,
  type EmployeeApprovalRecord,
} from "../api";
import { ErrorState, LoadingState } from "../components/AsyncState";
import { usePageAssistantContext } from "../hooks/usePageAssistantContext";
import { usePermissions } from "../hooks/usePermissions";
import { label, LIFECYCLE_STATUS, LIFECYCLE_PHASE, MATURITY, RISK_LEVEL } from "../lib/labels";

const TABS = [
  "Resumen",
  "Configuración",
  "Conocimiento",
  "Herramientas",
  "Modelo",
  "Automatizaciones",
  "Límites",
  "Versiones",
  "Pruebas",
  "Aprobación",
  "Publicación",
  "Historial",
] as const;

export function EmployeeDetailPage() {
  const { employeeId } = useParams<{ employeeId: string }>();
  const [searchParams] = useSearchParams();
  const { has } = usePermissions();
  const canEdit = has("employee.edit");
  const canApprove = has("employee.approve");
  const canTrain = has("employee.train");
  const findingId = searchParams.get("finding_id");
  const auditRunId = searchParams.get("audit_run_id");
  const correlationId = searchParams.get("correlation_id");
  const traceIdParam = searchParams.get("trace_id");
  const tabParam = searchParams.get("tab");
  const [tab, setTab] = useState<(typeof TABS)[number]>("Resumen");
  const [auditContext, setAuditContext] = useState<Record<string, unknown> | null>(null);
  const [traceId, setTraceId] = useState<string | null>(traceIdParam);
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);
  const [inventory, setInventory] = useState<Record<string, unknown> | null>(null);
  const [health, setHealth] = useState<Record<string, unknown> | null>(null);
  const [versions, setVersions] = useState<Array<Record<string, unknown>>>([]);
  const [approvals, setApprovals] = useState<EmployeeApprovalRecord[]>([]);
  const [validation, setValidation] = useState<Record<string, unknown> | null>(null);
  const [capAssignments, setCapAssignments] = useState<{ assigned: CatalogItem[]; available: CatalogItem[] }>({ assigned: [], available: [] });
  const [toolAssignments, setToolAssignments] = useState<{ assigned: CatalogItem[]; available: CatalogItem[] }>({ assigned: [], available: [] });
  const [knowledgeAssignments, setKnowledgeAssignments] = useState<{ assigned: CatalogItem[]; available: CatalogItem[] }>({ assigned: [], available: [] });
  const [testResult, setTestResult] = useState<Record<string, unknown> | null>(null);
  const [certResult, setCertResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  usePageAssistantContext(
    {
      empleado_id: employeeId,
      tab,
      nombre: detail?.name,
      estado: detail?.lifecycle_status,
      especialidad: detail?.specialty,
    },
    Boolean(employeeId),
  );

  async function load() {
    if (!employeeId) return;
    try {
      const [d, caps, tools, knowledge, inv, h, vers, appr] = await Promise.all([
        fetchEmployeeDetail(employeeId),
        fetchEmployeeCapabilities(employeeId),
        fetchEmployeeTools(employeeId),
        fetchEmployeeKnowledge(employeeId),
        fetchEmployeeInventory(employeeId),
        fetchEmployeeHealth(employeeId),
        fetchEmployeeVersions(employeeId),
        fetchEmployeeApprovals(employeeId),
      ]);
      setDetail(d);
      setInventory(inv);
      setHealth(h);
      setVersions(vers);
      setApprovals(appr);
      setCapAssignments(caps);
      setToolAssignments(tools);
      setKnowledgeAssignments(knowledge);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Error al cargar el empleado.");
    }
  }

  useEffect(() => { load(); }, [employeeId]);

  useEffect(() => {
    if (tabParam && TABS.includes(tabParam as (typeof TABS)[number])) {
      setTab(tabParam as (typeof TABS)[number]);
    }
  }, [tabParam]);

  useEffect(() => {
    if (!findingId) return;
    if (traceIdParam) {
      setTraceId(traceIdParam);
      return;
    }
    iniciarMejoraAuditor(findingId, `ui:${findingId}`)
      .then((res) => {
        setTraceId(String(res.trace_id || ""));
        setAuditContext(res);
      })
      .catch(() => {
        /* el usuario puede continuar en fábrica sin traza */
      });
  }, [findingId, traceIdParam]);

  useEffect(() => {
    if (traceId) {
      fetchMejoraTrazabilidad(traceId).then(setAuditContext).catch(() => undefined);
    }
  }, [traceId]);

  async function runAction(action: "test" | "certify" | "publish" | "activate" | "validate") {
    if (!employeeId) return;
    setLoading(true);
    setError(null);
    try {
      if (action === "test") setTestResult(await testEmployee(employeeId));
      if (action === "certify") setCertResult(await certifyEmployee(employeeId));
      if (action === "publish") await publishEmployee(employeeId);
      if (action === "activate") await activateEmployee(employeeId);
      if (action === "validate") setValidation(await validateEmployee(employeeId));
      await load();
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : "No se pudo completar la acción.";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  }

  async function handleAssign(type: "cap" | "tool" | "knowledge", id: string) {
    if (!employeeId) return;
    setError(null);
    try {
      if (type === "cap") await assignEmployeeCapability(employeeId, id);
      if (type === "tool") await assignEmployeeTool(employeeId, id);
      if (type === "knowledge") await assignEmployeeKnowledge(employeeId, id);
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Error al asignar");
    }
  }

  async function handleRemove(type: "cap" | "tool" | "knowledge", id: string) {
    if (!employeeId) return;
    setError(null);
    try {
      if (type === "cap") await removeEmployeeCapability(employeeId, id);
      if (type === "tool") await removeEmployeeTool(employeeId, id);
      if (type === "knowledge") await removeEmployeeKnowledge(employeeId, id);
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Error al retirar");
    }
  }

  async function handleTrain() {
    if (!employeeId) return;
    setLoading(true);
    try {
      await trainEmployee(employeeId, {
        training_type: "INSTRUCTIONS",
        reason: "Capacitación manual desde ficha",
        source: "ui-empleado",
        config_delta: { instructions: { operating_rules: "Procedimiento actualizado desde UI" } },
      });
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Error en capacitación");
    } finally {
      setLoading(false);
    }
  }

  async function handleRetire() {
    if (!employeeId || !window.confirm("¿Retirar este empleado IA?")) return;
    setLoading(true);
    try {
      await retireEmployee(employeeId, "Retiro solicitado desde ficha de empleado");
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Error al retirar");
    } finally {
      setLoading(false);
    }
  }

  async function handleRequestApproval() {
    if (!employeeId) return;
    setLoading(true);
    setError(null);
    try {
      await requestEmployeeApproval(employeeId, {
        kind: "PUBLISH",
        reason: "Solicitud de publicación desde ficha de empleado",
      });
      setTab("Aprobación");
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "No se pudo solicitar aprobación.");
    } finally {
      setLoading(false);
    }
  }

  async function handleDecideApproval(approvalRequestId: string, decision: "approve" | "reject") {
    if (!employeeId) return;
    const comment = decision === "reject"
      ? window.prompt("Motivo del rechazo (opcional)") || undefined
      : undefined;
    setLoading(true);
    setError(null);
    try {
      await decideEmployeeApproval(employeeId, approvalRequestId, decision, comment);
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "No se pudo procesar la decisión.");
    } finally {
      setLoading(false);
    }
  }

  if (!detail && !error) return <LoadingState message="Cargando empleado…" />;
  if (error && !detail) return <ErrorState message={error} onRetry={load} />;

  const lifecycle = String(detail?.lifecycle_status || "");
  const phase = String(inventory?.lifecycle_phase || detail?.lifecycle_phase || "");
  const caps = (detail?.capabilities as Array<{ code: string; name: string }>) || [];
  const model = inventory?.model as Record<string, unknown> | undefined;
  const limits = inventory?.limits as Record<string, unknown> | undefined;
  const finops = inventory?.finops as Record<string, unknown> | undefined;
  const automations = (inventory?.automations as Array<Record<string, unknown>>) || [];

  return (
    <div className="ops-page">
      <header className="page-header">
        <Link to="/directorio" className="muted">← Directorio</Link>
        {findingId && <Link to="/trabajo" className="muted"> · Mi Trabajo</Link>}
        <h1>{String(detail?.name || "Empleado")}</h1>
        <span className={`badge status-${lifecycle}`} title={lifecycle}>
          {label(LIFECYCLE_STATUS, lifecycle)}
        </span>
        {phase && <span className="badge muted">{label(LIFECYCLE_PHASE, phase) || phase}</span>}
      </header>

      {findingId && (
        <section className="panel muted auditor-context-banner">
          <p><strong>Contexto Auditor</strong> — hallazgo vinculado desde Mi Trabajo.</p>
          <p className="mono small">
            Hallazgo: {findingId.slice(0, 8)}…
            {auditRunId ? ` · Ejecución: ${auditRunId.slice(0, 8)}…` : ""}
            {correlationId ? ` · Correlación: ${correlationId.slice(0, 8)}…` : ""}
            {traceId ? ` · Traza: ${traceId.slice(0, 8)}…` : ""}
          </p>
          {auditContext?.outcome_classification ? (
            <p>Resultado: {String(auditContext.outcome_classification)}</p>
          ) : (
            <p className="muted">Las acciones de fábrica aplican guardas RBAC y aprobación existentes. El Auditor no ejecuta cambios automáticamente.</p>
          )}
          {traceId && canTrain && tab === "Resumen" && (
            <div className="ops-actions">
              <button
                type="button"
                className="btn"
                disabled={loading}
                onClick={async () => {
                  if (!traceId) return;
                  setLoading(true);
                  try {
                    await ejecutarMejoraFabrica(traceId, {
                      operation: "capacitar",
                      payload: {
                        training_type: "INSTRUCTIONS",
                        reason: "Capacitación desde contexto Auditor",
                        source: "auditor-fabrica-ui",
                        config_delta: { instructions: { operating_rules: "Procedimiento actualizado tras hallazgo Auditor" } },
                      },
                      idempotency_key: `train:${traceId}`,
                    });
                    await load();
                    await fetchMejoraTrazabilidad(traceId).then(setAuditContext);
                  } catch (e) {
                    setError(e instanceof ApiError ? e.message : "No se pudo capacitar");
                  } finally {
                    setLoading(false);
                  }
                }}
              >
                Capacitar (autorizado)
              </button>
              <button
                type="button"
                className="btn"
                disabled={loading}
                onClick={async () => {
                  if (!traceId) return;
                  setLoading(true);
                  try {
                    await ejecutarMejoraFabrica(traceId, { operation: "probar", idempotency_key: `test:${traceId}` });
                    await load();
                  } catch (e) {
                    setError(e instanceof ApiError ? e.message : "No se pudieron ejecutar pruebas");
                  } finally {
                    setLoading(false);
                  }
                }}
              >
                Ejecutar pruebas
              </button>
              <button
                type="button"
                className="btn"
                disabled={loading}
                onClick={async () => {
                  if (!traceId) return;
                  setLoading(true);
                  try {
                    await reauditarMejora(traceId, `reaudit:${traceId}`);
                    await fetchMejoraTrazabilidad(traceId).then(setAuditContext);
                  } catch (e) {
                    setError(e instanceof ApiError ? e.message : "No se pudo reauditar");
                  } finally {
                    setLoading(false);
                  }
                }}
              >
                Solicitar reauditoría
              </button>
            </div>
          )}
        </section>
      )}

      <div className="tab-bar compact-tab-bar">
        {TABS.map((t) => (
          <button key={t} type="button" className={`tab-btn ${tab === t ? "active" : ""}`} onClick={() => setTab(t)}>{t}</button>
        ))}
      </div>

      <section className="panel">
        {tab === "Resumen" && (
          <>
            <p className="mono muted">{String(detail?.code)} · v{String(detail?.version)}</p>
            <p><strong>Fase:</strong> {label(LIFECYCLE_PHASE, phase) || phase || "—"}</p>
            <p><strong>Especialidad:</strong> {String(detail?.specialty)}</p>
            <p><strong>Objetivo:</strong> {String(inventory?.objective || detail?.objective || "—")}</p>
            <p><strong>Riesgo:</strong> {label(RISK_LEVEL, String(detail?.risk_level))} · <strong>Madurez:</strong> {label(MATURITY, String(detail?.maturity))}</p>
            {health && (
              <ul className="compact-list muted">
                <li>Última prueba: {String(health.last_test_result || "—")} {health.last_test_at ? `(${String(health.last_test_at).slice(0, 19)})` : ""}</li>
                <li>Última publicación: {health.last_publication ? String(health.last_publication).slice(0, 19) : "—"}</li>
                <li>Última capacitación: {health.last_training_at ? String(health.last_training_at).slice(0, 19) : "—"}</li>
              </ul>
            )}
            <div className="ops-actions">
              <Link className="btn" to={`/empleados/${employeeId}/editar`}>Editar configuración</Link>
              <button type="button" className="btn" disabled={loading} onClick={() => runAction("validate")}>Validar</button>
              <button type="button" className="btn" disabled={loading} onClick={() => runAction("test")}>Ejecutar pruebas</button>
              <button type="button" className="btn" disabled={loading} onClick={() => runAction("certify")}>Certificar</button>
              {canEdit && (
                <button type="button" className="btn" disabled={loading} onClick={handleRequestApproval}>Solicitar aprobación</button>
              )}
              <button type="button" className="btn primary" disabled={loading || lifecycle !== "CERTIFIED"} onClick={() => runAction("publish")}>Publicar</button>
              <button type="button" className="btn primary" disabled={loading || !["PUBLISHED", "PAUSED"].includes(lifecycle)} onClick={() => runAction("activate")}>Activar</button>
              <button type="button" className="btn" disabled={loading} onClick={handleTrain}>Capacitar</button>
              <button type="button" className="btn danger" disabled={loading} onClick={handleRetire}>Retirar</button>
            </div>
            {validation && <pre className="mono result-pre">{JSON.stringify(validation, null, 2)}</pre>}
          </>
        )}

        {tab === "Configuración" && (
          <>
            <p><strong>Rol:</strong> {String(inventory?.role || "—")}</p>
            <p><strong>Responsabilidades:</strong> {String(inventory?.responsibilities || "—")}</p>
            <p><strong>Capacidades:</strong> {caps.map((c) => c.code || c).join(", ") || "—"}</p>
            <Link className="btn" to={`/empleados/${employeeId}/editar`}>Abrir asistente de configuración</Link>
          </>
        )}

        {tab === "Conocimiento" && (
          <div>
            <h3>Fuentes asignadas (930)</h3>
            <ul className="assign-list">
              {knowledgeAssignments.assigned.map((k) => (
                <li key={k.id}>{k.name} <button type="button" className="btn-link" onClick={() => handleRemove("knowledge", k.id)}>Retirar</button></li>
              ))}
            </ul>
            <h4>Disponibles</h4>
            <ul className="assign-list">
              {knowledgeAssignments.available.map((k) => (
                <li key={k.id}>{k.name} <button type="button" className="btn-link" onClick={() => handleAssign("knowledge", k.id)}>Asignar</button></li>
              ))}
            </ul>
          </div>
        )}

        {tab === "Herramientas" && (
          <div>
            <ul className="assign-list">
              {toolAssignments.assigned.map((t) => (
                <li key={t.id}>{t.name} <button type="button" className="btn-link" onClick={() => handleRemove("tool", t.id)}>Retirar</button></li>
              ))}
            </ul>
            <h4>Disponibles</h4>
            <ul className="assign-list">
              {toolAssignments.available.map((t) => (
                <li key={t.id}>{t.name} <button type="button" className="btn-link" onClick={() => handleAssign("tool", t.id)}>Asignar</button></li>
              ))}
            </ul>
          </div>
        )}

        {tab === "Modelo" && (
          <>
            <p><strong>Proveedor:</strong> {String(model?.provider || "—")}</p>
            <p><strong>Modelo:</strong> {String(model?.model || "—")}</p>
            <p><strong>Modelo de respaldo:</strong> {String(model?.fallback_model || "—")}</p>
            <p className="muted">Las credenciales permanecen en infraestructura segura (sin secretos en el empleado).</p>
          </>
        )}

        {tab === "Automatizaciones" && (
          automations.length === 0 ? (
            <p className="muted">Sin automatizaciones vinculadas. <Link to="/automatizaciones">Gestionar automatizaciones</Link></p>
          ) : (
            <ul>{automations.map((a) => <li key={String(a.id)}>{String(a.name)} — {String(a.status)}</li>)}</ul>
          )
        )}

        {tab === "Límites" && (
          <>
            <p><strong>Tiempo límite:</strong> {String(limits?.timeout_seconds ?? "—")}s</p>
            <p><strong>Tareas concurrentes:</strong> {String(limits?.max_concurrent_tasks ?? "—")}</p>
            <p><strong>Presupuesto diario:</strong> {finops?.budget_daily != null ? String(finops.budget_daily) : "—"}</p>
            <p><strong>Límite costo diario:</strong> {finops?.daily_cost_limit != null ? String(finops.daily_cost_limit) : "—"}</p>
          </>
        )}

        {tab === "Versiones" && (
          <table className="data-table">
            <thead><tr><th>Versión</th><th>Estado</th><th>Motivo</th><th>Fecha</th><th></th></tr></thead>
            <tbody>
              {versions.map((v) => (
                <tr key={String(v.id)}>
                  <td>{String(v.version)}</td>
                  <td>{String(v.status)}</td>
                  <td>{String(v.change_reason || "—")}</td>
                  <td className="mono">{String(v.created_at).slice(0, 19)}</td>
                  <td>
                    {Number(v.version) < Number(detail?.version) && (
                      <button
                        type="button"
                        className="btn-link"
                        onClick={() => employeeId && rollbackEmployee(employeeId, { target_version: Number(v.version), reason: "Rollback desde UI" }).then(load)}
                      >
                        Restaurar
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {tab === "Pruebas" && (
          <>
            {(detail?.test_cases as Array<Record<string, unknown>>)?.map((tc) => (
              <p key={String(tc.id)}>{String(tc.name)} — {String(tc.test_category || tc.test_type)}</p>
            ))}
            {testResult ? <pre className="mono result-pre">{JSON.stringify(testResult, null, 2)}</pre> : <p className="muted">Ejecute pruebas desde Resumen.</p>}
          </>
        )}

        {tab === "Aprobación" && (
          <>
            <p className="muted">Solicitudes de aprobación vinculadas a este empleado. Las acciones respetan RBAC.</p>
            {canEdit && (
              <button type="button" className="btn" disabled={loading} onClick={handleRequestApproval}>
                Solicitar aprobación de publicación
              </button>
            )}
            {approvals.length === 0 ? (
              <p className="muted">Sin solicitudes de aprobación registradas.</p>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Estado</th>
                    <th>Tipo</th>
                    <th>Solicitado</th>
                    <th>Solicitante</th>
                    <th>Aprobador</th>
                    <th>Resultado</th>
                    <th>Comentario</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {approvals.map((item) => (
                    <tr key={item.factory_approval_id}>
                      <td>{item.status}</td>
                      <td>{item.approval_kind}</td>
                      <td className="mono">{new Date(item.requested_at).toLocaleString()}</td>
                      <td>{item.requested_by_name || item.requested_by_id}</td>
                      <td>{item.decided_by_name || (item.approval_status === "PENDING" ? "—" : "—")}</td>
                      <td>{item.approval_status}</td>
                      <td className="cell-truncate" title={item.decision_comment || item.reason}>
                        {item.decision_comment || item.reason}
                      </td>
                      <td>
                        {canApprove && item.can_decide && item.approval_status === "PENDING" && (
                          <span className="notification-actions">
                            <button type="button" className="btn" disabled={loading} onClick={() => handleDecideApproval(item.approval_request_id, "approve")} title="Aprobar">✓</button>
                            <button type="button" className="btn" disabled={loading} onClick={() => handleDecideApproval(item.approval_request_id, "reject")} title="Rechazar">×</button>
                          </span>
                        )}
                        {item.approval_status === "PENDING" && !item.can_decide && canApprove && (
                          <span className="muted" title="No puede aprobar su propia solicitud">Segregación</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </>
        )}

        {tab === "Publicación" && (
          <>
            <p><strong>Estado:</strong> {label(LIFECYCLE_STATUS, lifecycle)}</p>
            <p><strong>Certificaciones:</strong></p>
            {(detail?.certifications as Array<Record<string, unknown>>)?.map((c) => (
              <p key={String(c.id)}>{String(c.result)} — score {String(c.score)} (v{String(c.version)})</p>
            ))}
            {certResult && <pre className="mono result-pre">{JSON.stringify(certResult, null, 2)}</pre>}
          </>
        )}

        {tab === "Historial" && (
          <p className="muted">Estado operativo: {String(detail?.status)} · Versión activa: v{String(health?.active_version ?? detail?.version)}</p>
        )}
        {error && <p className="error">{error}</p>}
      </section>
    </div>
  );
}
