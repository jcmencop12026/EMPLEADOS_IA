import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  activateEmployee,
  ApiError,
  certifyEmployee,
  fetchEmployeeDetail,
  publishEmployee,
  testEmployee,
} from "../api";
import { ErrorState, LoadingState } from "../components/AsyncState";
import { label, LIFECYCLE_STATUS, MATURITY, RISK_LEVEL } from "../lib/labels";

const TABS = ["Resumen", "Pruebas", "Certificación", "Versiones", "Actividad"] as const;

export function EmployeeDetailPage() {
  const { employeeId } = useParams<{ employeeId: string }>();
  const [tab, setTab] = useState<(typeof TABS)[number]>("Resumen");
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);
  const [testResult, setTestResult] = useState<Record<string, unknown> | null>(null);
  const [certResult, setCertResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function load() {
    if (!employeeId) return;
    try {
      setDetail(await fetchEmployeeDetail(employeeId));
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
            <p><strong>Capabilities:</strong> {caps.map((c) => c.code || c).join(", ") || (detail?.capabilities as string[])?.join(", ")}</p>
            <div className="ops-actions">
              <Link className="btn" to={`/empleados/${employeeId}/editar`}>Editar configuración</Link>
              <button type="button" className="btn" disabled={loading} onClick={() => runAction("test")}>Ejecutar pruebas</button>
              <button type="button" className="btn" disabled={loading} onClick={() => runAction("certify")}>Certificar</button>
              <button type="button" className="btn primary" disabled={loading || lifecycle !== "CERTIFIED"} onClick={() => runAction("publish")}>Publicar</button>
              <button type="button" className="btn primary" disabled={loading || !["PUBLISHED", "PAUSED"].includes(lifecycle)} onClick={() => runAction("activate")}>Activar</button>
            </div>
          </>
        )}
        {tab === "Pruebas" && (
          <>
            {testResult ? (
              <pre className="mono result-pre">{JSON.stringify(testResult, null, 2)}</pre>
            ) : (
              <p className="muted">Ejecute pruebas desde Resumen o Test Lab.</p>
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
