import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import type { ExecutionDetail, UserMe, WorkEventItem } from "../api";
import { api, decideApproval, fetchApprovals, fetchEvents, fetchExecution } from "../api";

export function ExecutionDetailPage() {
  const { planId } = useParams<{ planId: string }>();
  const [searchParams] = useSearchParams();
  const approvalId = searchParams.get("approval");
  const [detail, setDetail] = useState<ExecutionDetail | null>(null);
  const [events, setEvents] = useState<WorkEventItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [acting, setActing] = useState(false);
  const [canApprove, setCanApprove] = useState(false);

  async function load() {
    if (!planId) return;
    try {
      const [d, ev, approvals] = await Promise.all([
        fetchExecution(planId),
        fetchEvents(),
        fetchApprovals(),
      ]);
      setDetail(d);
      setEvents(ev.filter((e) => e.work_plan_id === planId));
      const pending = approvals.find((a) => a.work_plan_id === planId && (!approvalId || a.id === approvalId));
      if (pending && d.approval_status === "PENDING") {
        setDetail({ ...d, approval_status: "PENDING" });
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    }
  }

  useEffect(() => {
    let cancelled = false;

    const bootstrap = async () => {
      try {
        const me = await api<UserMe>("/api/auth/me");
        if (!cancelled) {
          setCanApprove(me.permissions.includes("operations.approve"));
        }
      } catch {
        if (!cancelled) {
          setCanApprove(false);
        }
      }
      if (!cancelled) {
        await load();
      }
    };

    void bootstrap();

    return () => {
      cancelled = true;
    };
  }, [planId]);

  async function handleApproval(decision: "approve" | "reject") {
    if (!planId) return;
    setActing(true);
    try {
      const approvals = await fetchApprovals();
      const pending = approvals.find((a) => a.work_plan_id === planId && (!approvalId || a.id === approvalId));
      if (!pending) return;
      const res = await decideApproval(pending.id, decision);
      setDetail(res);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    } finally {
      setActing(false);
    }
  }

  if (!detail && !error) return <p className="muted">Cargando…</p>;

  return (
    <div className="ops-page">
      <header className="page-header">
        <Link to="/ejecuciones" className="muted">
          ← Ejecuciones
        </Link>
        <h1>Detalle de ejecución</h1>
      </header>
      {error && <p className="error">{error}</p>}
      {detail && (
        <>
          <section className="panel">
            <div className="result-header">
              <span className={`badge status-${detail.status}`}>{detail.status}</span>
              <span className="muted mono">{detail.correlation_id}</span>
            </div>
            <p><strong>Objetivo:</strong> {detail.objective}</p>
            <p>{detail.summary}</p>
            {detail.confidence != null && (
              <p className="muted">Confianza: {(detail.confidence * 100).toFixed(0)}%</p>
            )}
            {detail.approval_status === "PENDING" && canApprove && (
              <div className="approval-box">
                <p className="warn">Aprobación humana requerida</p>
                <button type="button" className="btn primary" disabled={acting} onClick={() => void handleApproval("approve")}>
                  Aprobar
                </button>
                <button type="button" className="btn danger" disabled={acting} onClick={() => void handleApproval("reject")}>
                  Rechazar
                </button>
              </div>
            )}
            {detail.approval_status === "PENDING" && !canApprove && (
              <p className="muted">Aprobación pendiente — sin permiso para decidir.</p>
            )}
          </section>

          <section className="panel">
            <h2>Tareas</h2>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Título</th>
                  <th>Estado</th>
                  <th>Ejecutor</th>
                  <th>Confianza</th>
                </tr>
              </thead>
              <tbody>
                {(detail.tasks || []).map((t) => (
                  <tr key={t.id}>
                    <td>{t.title}</td>
                    <td>{t.status}</td>
                    <td className="mono">{t.executor_type}</td>
                    <td>{t.confidence != null ? `${(t.confidence * 100).toFixed(0)}%` : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="panel">
            <h2>Trazabilidad (eventos)</h2>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Evento</th>
                  <th>Tarea</th>
                  <th>Fecha</th>
                </tr>
              </thead>
              <tbody>
                {events.map((e) => (
                  <tr key={e.id}>
                    <td className="mono">{e.event_type}</td>
                    <td className="mono">{e.task_id?.slice(0, 8) || "—"}</td>
                    <td className="mono">{e.created_at?.slice(0, 19)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </>
      )}
    </div>
  );
}
