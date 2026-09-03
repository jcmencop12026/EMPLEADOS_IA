import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  activateEmployee,
  ApiError,
  assignEmployeeCapability,
  assignEmployeeKnowledge,
  assignEmployeeTool,
  certifyEmployee,
  fetchEmployeeCapabilities,
  fetchEmployeeDetail,
  fetchEmployeeKnowledge,
  fetchEmployeeTools,
  publishEmployee,
  removeEmployeeCapability,
  removeEmployeeKnowledge,
  removeEmployeeTool,
  testEmployee,
  type CatalogItem,
} from "../api";
import { ErrorState, LoadingState } from "../components/AsyncState";
import { EmployeeFicha20Tab } from "../components/EmployeeFicha20Tab";
import { label, LIFECYCLE_STATUS, MATURITY, RISK_LEVEL } from "../lib/labels";

const TABS = ["Resumen", "Ficha 2.0", "Asignaciones", "Pruebas", "Certificación", "Versiones", "Actividad"] as const;

export function EmployeeDetailPage() {
  const { employeeId } = useParams<{ employeeId: string }>();
  const [tab, setTab] = useState<(typeof TABS)[number]>("Resumen");
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);
  const [capAssignments, setCapAssignments] = useState<{ assigned: CatalogItem[]; available: CatalogItem[] }>({ assigned: [], available: [] });
  const [toolAssignments, setToolAssignments] = useState<{ assigned: CatalogItem[]; available: CatalogItem[] }>({ assigned: [], available: [] });
  const [knowledgeAssignments, setKnowledgeAssignments] = useState<{ assigned: CatalogItem[]; available: CatalogItem[] }>({ assigned: [], available: [] });
  const [testResult, setTestResult] = useState<Record<string, unknown> | null>(null);
  const [certResult, setCertResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function load() {
    if (!employeeId) return;
    try {
      const [d, caps, tools, knowledge] = await Promise.all([
        fetchEmployeeDetail(employeeId),
        fetchEmployeeCapabilities(employeeId),
        fetchEmployeeTools(employeeId),
        fetchEmployeeKnowledge(employeeId),
      ]);
      setDetail(d);
      setCapAssignments(caps);
      setToolAssignments(tools);
      setKnowledgeAssignments(knowledge);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Error al cargar el empleado.");
    }
  }

  useEffect(() => { load(); }, [employeeId]);

  async function runAction(action: "test" | "certify" | "publish" | "activate") {
    if (!employeeId) return;
    setLoading(true);
    setError(null);
    try {
      if (action === "test") setTestResult(await testEmployee(employeeId));
      if (action === "certify") setCertResult(await certifyEmployee(employeeId));
      if (action === "publish") await publishEmployee(employeeId);
      if (action === "activate") await activateEmployee(employeeId);
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "No se pudo completar la acción.");
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

  if (!detail && !error) return <LoadingState message="Cargando empleado…" />;
  if (error && !detail) return <ErrorState message={error} onRetry={load} />;

  const lifecycle = String(detail?.lifecycle_status || "");
  const caps = (detail?.capabilities as Array<{ code: string; name: string }>) || [];

  return (
    <div className="ops-page">
      <header className="page-header">
        <Link to="/directorio" className="muted">← Directorio</Link>
        <h1>{String(detail?.name || "Empleado")}</h1>
        <span className={`badge status-${lifecycle}`} title={lifecycle}>
          {label(LIFECYCLE_STATUS, lifecycle)}
        </span>
      </header>

      <div className="tab-bar">
        {TABS.map((t) => (
          <button key={t} type="button" className={`tab-btn ${tab === t ? "active" : ""}`} onClick={() => setTab(t)}>{t}</button>
        ))}
      </div>

      <section className="panel">
        {tab === "Resumen" && (
          <>
            <p className="mono muted">{String(detail?.code)} · v{String(detail?.version)}</p>
            <p><strong>Especialidad:</strong> {String(detail?.specialty)}</p>
            <p><strong>Riesgo:</strong> {label(RISK_LEVEL, String(detail?.risk_level))} · <strong>Madurez:</strong> {label(MATURITY, String(detail?.maturity))}</p>
            <p><strong>Capacidades:</strong> {caps.map((c) => c.code || c).join(", ") || (detail?.capabilities as string[])?.join(", ")}</p>
            <div className="ops-actions">
              <Link className="btn" to={`/empleados/${employeeId}/editar`}>Editar configuración</Link>
              <Link className="btn" to="/test-lab">Abrir Test Lab</Link>
              <button type="button" className="btn" disabled={loading} onClick={() => runAction("test")}>Ejecutar pruebas</button>
              <button type="button" className="btn" disabled={loading} onClick={() => runAction("certify")}>Certificar</button>
              <button type="button" className="btn primary" disabled={loading || lifecycle !== "CERTIFIED"} onClick={() => runAction("publish")}>Publicar</button>
              <button type="button" className="btn primary" disabled={loading || !["PUBLISHED", "PAUSED"].includes(lifecycle)} onClick={() => runAction("activate")}>Activar</button>
            </div>
          </>
        )}
        {tab === "Ficha 2.0" && employeeId && <EmployeeFicha20Tab employeeId={employeeId} />}
        {tab === "Asignaciones" && (
          <div className="assign-grid">
            <div>
              <h3>Capacidades asignadas</h3>
              <ul className="assign-list">
                {capAssignments.assigned.map((c) => (
                  <li key={c.id}>{c.name} <button type="button" className="btn-link" onClick={() => handleRemove("cap", c.id)}>Retirar</button></li>
                ))}
              </ul>
              <h4>Disponibles</h4>
              <ul className="assign-list">
                {capAssignments.available.map((c) => (
                  <li key={c.id}>{c.name} <button type="button" className="btn-link" onClick={() => handleAssign("cap", c.id)}>Asignar</button></li>
                ))}
              </ul>
            </div>
            <div>
              <h3>Herramientas asignadas</h3>
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
            <div>
              <h3>Fuentes asignadas</h3>
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
          </div>
        )}
        {tab === "Pruebas" && (
          <>
            {testResult ? (
              <pre className="mono result-pre">{JSON.stringify(testResult, null, 2)}</pre>
            ) : (
              <p className="muted">Ejecute pruebas desde Resumen o <Link to="/test-lab">Test Lab</Link>.</p>
            )}
          </>
        )}
        {tab === "Certificación" && (
          <>
            {(detail?.certifications as Array<Record<string, unknown>>)?.map((c) => (
              <p key={String(c.id)}>{String(c.result)} — score {String(c.score)} (v{String(c.version)})</p>
            ))}
            {certResult && <pre className="mono result-pre">{JSON.stringify(certResult, null, 2)}</pre>}
          </>
        )}
        {tab === "Versiones" && (
          <table className="data-table">
            <thead><tr><th>Versión</th><th>Estado</th><th>Fecha</th></tr></thead>
            <tbody>
              {((detail?.versions as Array<Record<string, unknown>>) || []).map((v) => (
                <tr key={String(v.id)}><td>{String(v.version)}</td><td>{label(LIFECYCLE_STATUS, String(v.status))}</td><td className="mono">{String(v.created_at).slice(0, 19)}</td></tr>
              ))}
            </tbody>
          </table>
        )}
        {tab === "Actividad" && <p className="muted">Estado operativo: {String(detail?.status)}</p>}
        {error && <p className="error">{error}</p>}
      </section>
    </div>
  );
}
