import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import type { OperationDetail } from "../api";
import {
  cancelOperation,
  fetchOperationActivity,
  fetchOperationApprovals,
  fetchOperationDetail,
  fetchOperationExecutions,
  fetchOperationResults,
  fetchOperationTasks,
  runOperation,
} from "../api";

type Tab = "resumen" | "plan" | "tareas" | "ejecuciones" | "aprobaciones" | "resultados" | "actividad";

export function OperationDetailPage() {
  const { operationId } = useParams<{ operationId: string }>();
  const [detail, setDetail] = useState<OperationDetail | null>(null);
  const [tasks, setTasks] = useState<Array<Record<string, unknown>>>([]);
  const [executions, setExecutions] = useState<Array<Record<string, unknown>>>([]);
  const [approvals, setApprovals] = useState<Array<Record<string, unknown>>>([]);
  const [results, setResults] = useState<Record<string, unknown> | null>(null);
  const [activity, setActivity] = useState<Array<Record<string, unknown>>>([]);
  const [tab, setTab] = useState<Tab>("resumen");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    if (!operationId) return;
    setLoading(true);
    setError("");
    try {
      const [d, t, e, a, r, act] = await Promise.all([
        fetchOperationDetail(operationId),
        fetchOperationTasks(operationId),
        fetchOperationExecutions(operationId),
        fetchOperationApprovals(operationId),
        fetchOperationResults(operationId),
        fetchOperationActivity(operationId),
      ]);
      setDetail(d);
      setTasks(t);
      setExecutions(e);
      setApprovals(a);
      setResults(r);
      setActivity(act);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [operationId]);

  if (loading) return <p className="muted">Cargando operación…</p>;
  if (!detail) return <p className="error">{error || "La operación no existe o no está disponible."}</p>;

  return (
    <div className="ops-page">
      <header className="page-header">
        <Link to="/operaciones" className="muted">
          ← Operaciones
        </Link>
        <h1>{detail.trabajo}</h1>
        <p className="muted">
          Estado: {detail.estado} · Progreso {detail.progreso}
        </p>
      </header>

      {error && <p className="error">{error}</p>}

      <div className="ops-actions">
        {detail.acciones.includes("iniciar") && (
          <button type="button" className="btn primary" title="Iniciar" onClick={() => void runOperation(detail.id).then(load)}>
            Iniciar
          </button>
        )}
        {detail.acciones.includes("cancelar") && (
          <button type="button" className="btn danger" title="Cancelar" onClick={() => void cancelOperation(detail.id).then(load)}>
            Cancelar
          </button>
        )}
      </div>

      <div className="tab-bar">
        {(
          [
            ["resumen", "Resumen"],
            ["plan", "Plan de trabajo"],
            ["tareas", "Tareas"],
            ["ejecuciones", "Ejecuciones"],
            ["aprobaciones", "Aprobaciones"],
            ["resultados", "Resultados"],
            ["actividad", "Actividad"],
          ] as Array<[Tab, string]>
        ).map(([key, label]) => (
          <button key={key} type="button" className={tab === key ? "active" : ""} onClick={() => setTab(key)}>
            {label}
          </button>
        ))}
      </div>

      {tab === "resumen" && (
        <section className="panel">
          <p>
            <strong>Objetivo:</strong> {detail.objective}
          </p>
          <p>
            <strong>Proceso:</strong> {detail.proceso || "—"}
          </p>
          <p>
            <strong>Responsable:</strong> {detail.responsable || "—"}
          </p>
          <p>
            <strong>Empleado IA:</strong> {detail.empleado_ia || "—"}
          </p>
          <p>
            <strong>Aprobación:</strong> {detail.approval_status}
          </p>
          {detail.summary && <p>{detail.summary}</p>}
          {detail.error && <p className="error">{detail.error}</p>}
        </section>
      )}

      {tab === "plan" && (
        <section className="panel">
          <p className="mono">{detail.correlation_id}</p>
          <p>{detail.objective}</p>
          {!detail.summary && <p className="muted">Sin plan detallado adicional.</p>}
        </section>
      )}

      {tab === "tareas" && (
        <section className="panel table-wrap">
          {tasks.length === 0 ? (
            <p className="muted">Sin tareas registradas.</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Tarea</th>
                  <th>Responsable</th>
                  <th>Estado</th>
                  <th>Resultado</th>
                  <th>Error</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map((task) => (
                  <tr key={String(task.id)}>
                    <td>{String(task.titulo)}</td>
                    <td>{String(task.responsable || "—")}</td>
                    <td>{String(task.estado)}</td>
                    <td>{String(task.resultado || "—")}</td>
                    <td>{String(task.error || "—")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}

      {tab === "ejecuciones" && (
        <section className="panel table-wrap">
          {executions.length === 0 ? (
            <p className="muted">Sin ejecuciones registradas.</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Inicio</th>
                  <th>Fin</th>
                  <th>Duración</th>
                  <th>Estado</th>
                  <th>Empleado IA</th>
                  <th>Resultado</th>
                </tr>
              </thead>
              <tbody>
                {executions.map((row) => (
                  <tr key={String(row.id)}>
                    <td>{row.inicio ? new Date(String(row.inicio)).toLocaleString() : "—"}</td>
                    <td>{row.fin ? new Date(String(row.fin)).toLocaleString() : "—"}</td>
                    <td>{row.duracion_ms ? `${row.duracion_ms} ms` : "—"}</td>
                    <td>{String(row.estado)}</td>
                    <td>{String(row.empleado_ia || "—")}</td>
                    <td className="cell-truncate">{String(row.resultado || row.error || "—")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}

      {tab === "aprobaciones" && (
        <section className="panel table-wrap">
          {approvals.length === 0 ? (
            <p className="muted">Sin aprobaciones registradas.</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Estado</th>
                  <th>Acción</th>
                  <th>Responsable</th>
                  <th>Fecha</th>
                  <th>Comentario</th>
                </tr>
              </thead>
              <tbody>
                {approvals.map((row) => (
                  <tr key={String(row.id)}>
                    <td>{String(row.estado)}</td>
                    <td>{String(row.accion)}</td>
                    <td>{String(row.responsable || "—")}</td>
                    <td>{row.fecha ? new Date(String(row.fecha)).toLocaleString() : "—"}</td>
                    <td>{String(row.comentario || "—")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}

      {tab === "resultados" && (
        <section className="panel">
          {!results?.resumen && !results?.resultado ? (
            <p className="muted">Sin resultados disponibles.</p>
          ) : (
            <>
              <p>{String(results.resumen || "")}</p>
              {results.resultado ? (
                <pre className="mono">{JSON.stringify(results.resultado, null, 2)}</pre>
              ) : null}
            </>
          )}
        </section>
      )}

      {tab === "actividad" && (
        <section className="panel table-wrap">
          {activity.length === 0 ? (
            <p className="muted">Sin actividad registrada.</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Evento</th>
                  <th>Detalle</th>
                </tr>
              </thead>
              <tbody>
                {activity.map((row) => (
                  <tr key={String(row.id)}>
                    <td>{row.fecha ? new Date(String(row.fecha)).toLocaleString() : "—"}</td>
                    <td>{String(row.etiqueta)}</td>
                    <td className="cell-truncate">{String(row.detalle || "—")}</td>
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
