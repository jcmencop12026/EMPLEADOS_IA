import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import type { OpportunityItem, OpportunityTrace } from "../api";
import {
  activateOpportunity,
  addOpportunityTracking,
  approveOpportunity,
  decideApproval,
  evaluateOpportunity,
  fetchExecution,
  fetchOperationApprovals,
  fetchOpportunity,
  fetchOpportunityEconomics,
  fetchOpportunityTrace,
  registerOpportunityResult,
  runOperation,
  type FinOpsOpportunityEconomics,
} from "../api";
import { usePermissions } from "../hooks/usePermissions";

type Tab = "resumen" | "evidencia" | "seguimiento" | "resultado" | "ejecucion" | "trazabilidad" | "finops";

const TABS: { id: Tab; label: string }[] = [
  { id: "resumen", label: "Resumen" },
  { id: "evidencia", label: "Evidencia" },
  { id: "seguimiento", label: "Seguimiento" },
  { id: "resultado", label: "Resultado" },
  { id: "ejecucion", label: "Ejecución" },
  { id: "trazabilidad", label: "Trazabilidad" },
  { id: "finops", label: "FinOps" },
];

const ESTADO_LABELS: Record<string, string> = {
  DETECTADA: "Detectada",
  EN_EVALUACION: "En evaluación",
  PRIORIZADA: "Priorizada",
  PROPUESTA: "Propuesta",
  PENDIENTE_APROBACION: "Pendiente aprobación",
  APROBADA: "Aprobada",
  EN_EJECUCION: "En ejecución",
  EN_SEGUIMIENTO: "En seguimiento",
  MATERIALIZADA: "Materializada",
  CERRADA: "Cerrada",
  DESCARTADA: "Descartada",
  CANCELADA: "Cancelada",
  FALLIDA: "Fallida",
  DATOS_INSUFICIENTES: "Datos insuficientes",
  NO_PERTINENTE: "No pertinente",
  SIN_CAPACIDAD: "Sin capacidad",
  POSPUESTA: "Pospuesta",
};

function formatMoney(v: number | null | undefined): string {
  if (v == null) return "—";
  return new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(v);
}

function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  return new Date(value).toLocaleString("es-CO");
}

function estadoLabel(estado: string): string {
  return ESTADO_LABELS[estado] ?? estado;
}

function JsonBlock({ value }: { value: unknown }) {
  if (value == null) return <p className="muted">Sin datos</p>;
  if (typeof value === "string") return <p>{value}</p>;
  return <pre className="json-block">{JSON.stringify(value, null, 2)}</pre>;
}

export function OportunidadDetailPage() {
  const { opportunityId } = useParams<{ opportunityId: string }>();
  const { has, loading: permsLoading } = usePermissions();
  const [opp, setOpp] = useState<OpportunityItem | null>(null);
  const [trace, setTrace] = useState<OpportunityTrace | null>(null);
  const [economics, setEconomics] = useState<FinOpsOpportunityEconomics | null>(null);
  const [tab, setTab] = useState<Tab>("resumen");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [autoExecute, setAutoExecute] = useState(false);
  const [planApprovals, setPlanApprovals] = useState<Array<Record<string, unknown>>>([]);
  const [planStatus, setPlanStatus] = useState<string | null>(null);

  const [trackAccion, setTrackAccion] = useState("");
  const [trackObs, setTrackObs] = useState("");
  const [resultValor, setResultValor] = useState("");
  const [resultEsperado, setResultEsperado] = useState("");
  const [resultEvidencia, setResultEvidencia] = useState("");
  const [resultEstado, setResultEstado] = useState("EXITO");
  const [rejectMotivo, setRejectMotivo] = useState("");

  const canEvaluate = has("oportunidades.evaluate");
  const canApprove = has("oportunidades.approve");
  const canActivate = has("oportunidades.activate");
  const canManage = has("oportunidades.manage");
  const canRunOps = has("operations.manage");
  const canDecideApproval = has("operations.approve");

  async function reload() {
    if (!opportunityId) return;
    setLoading(true);
    setError(null);
    try {
      const [o, t, eco] = await Promise.all([
        fetchOpportunity(opportunityId),
        fetchOpportunityTrace(opportunityId),
        fetchOpportunityEconomics(opportunityId).catch(() => null),
      ]);
      setOpp(o);
      setTrace(t);
      setEconomics(eco);
      if (o.work_plan_id) {
        const [approvals, execution] = await Promise.all([
          fetchOperationApprovals(o.work_plan_id).catch(() => []),
          fetchExecution(o.work_plan_id).catch(() => null),
        ]);
        setPlanApprovals(approvals as Array<Record<string, unknown>>);
        setPlanStatus(execution?.status ?? null);
      } else {
        setPlanApprovals([]);
        setPlanStatus(null);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar la oportunidad");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void reload();
  }, [opportunityId]);

  const accion = opp?.siguiente_accion ?? null;
  const equipo = opp?.equipo ?? null;
  const liderId = (equipo?.lider as Record<string, unknown> | undefined)?.employee_id as string | undefined;

  const chainSteps = useMemo(() => {
    if (!opp) return [];
    const steps: Array<{ label: string; done: boolean; link?: string }> = [
      { label: "Oportunidad detectada", done: true, link: `/oportunidades/${opp.id}` },
      { label: "Acción definida", done: Boolean(accion) },
      { label: "Aprobación", done: ["APROBADA", "EN_EJECUCION", "EN_SEGUIMIENTO", "MATERIALIZADA", "CERRADA"].includes(opp.estado) },
      { label: "Plan de trabajo", done: Boolean(opp.work_plan_id), link: opp.work_plan_id ? `/operaciones/${opp.work_plan_id}` : undefined },
      { label: "Ejecución", done: Boolean(opp.work_plan_id && planStatus && planStatus !== "READY"), link: opp.work_plan_id ? `/ejecuciones/${opp.work_plan_id}` : undefined },
      { label: "Resultado", done: Boolean(opp.resultado), link: opp.work_plan_id ? `/operaciones/${opp.work_plan_id}` : undefined },
      { label: "Materialización", done: opp.estado === "MATERIALIZADA" || (opp.valor_materializado ?? 0) > 0 },
    ];
    return steps;
  }, [opp, accion, planStatus]);

  async function onEvaluar() {
    if (!opportunityId) return;
    try {
      await evaluateOpportunity(opportunityId);
      setMsg("Evaluación completada");
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al evaluar");
    }
  }

  async function onAprobar() {
    if (!opportunityId) return;
    try {
      await approveOpportunity(opportunityId, true, "Aprobación desde centro de oportunidades");
      setMsg("Oportunidad aprobada");
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al aprobar");
    }
  }

  async function onRechazar() {
    if (!opportunityId) return;
    try {
      await approveOpportunity(opportunityId, false, rejectMotivo || "Rechazada desde centro de oportunidades");
      setMsg("Oportunidad rechazada");
      setRejectMotivo("");
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al rechazar");
    }
  }

  async function onActivar() {
    if (!opportunityId) return;
    try {
      await activateOpportunity(opportunityId, autoExecute);
      setMsg(autoExecute ? "Oportunidad activada y ejecución iniciada" : "Oportunidad activada — plan creado");
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al activar");
    }
  }

  async function onRunPlan() {
    if (!opp?.work_plan_id) return;
    try {
      await runOperation(opp.work_plan_id);
      setMsg("Ejecución del plan iniciada");
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al ejecutar el plan");
    }
  }

  async function onDecideApproval(approvalId: string, decision: "approve" | "reject") {
    try {
      await decideApproval(approvalId, decision, decision === "approve" ? "Aprobado desde oportunidad" : "Rechazado desde oportunidad");
      setMsg(decision === "approve" ? "Aprobación registrada" : "Rechazo registrado");
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error en decisión de aprobación");
    }
  }

  async function onAddTracking(e: FormEvent) {
    e.preventDefault();
    if (!opportunityId || !trackAccion.trim()) return;
    try {
      await addOpportunityTracking(opportunityId, { accion: trackAccion.trim(), bloqueo: trackObs.trim() || undefined });
      setTrackAccion("");
      setTrackObs("");
      setMsg("Seguimiento registrado");
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al registrar seguimiento");
    }
  }

  async function onRegisterResult(e: FormEvent) {
    e.preventDefault();
    if (!opportunityId) return;
    try {
      const evidencia = resultEvidencia.trim() ? { nota: resultEvidencia.trim() } : undefined;
      await registerOpportunityResult(opportunityId, {
        valor_real: resultValor ? Number(resultValor) : undefined,
        valor_esperado: resultEsperado ? Number(resultEsperado) : undefined,
        evidencia,
        estado_resultado: resultEstado,
      });
      setMsg("Resultado registrado — oportunidad materializada");
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al registrar resultado");
    }
  }

  if (loading || permsLoading) {
    return (
      <div className="ops-page">
        <p className="muted">Cargando oportunidad…</p>
      </div>
    );
  }

  if (!opp) {
    return (
      <div className="ops-page">
        <p className="error">{error ?? "Oportunidad no encontrada"}</p>
        <p><Link to="/oportunidades">← Volver al centro</Link></p>
      </div>
    );
  }

  const pendingApprovals = planApprovals.filter((a) => a.status === "PENDING");

  return (
    <div className="ops-page">
      <header className="page-header compact">
        <p><Link to="/oportunidades">← Centro de oportunidades</Link></p>
        <h1>{opp.titulo}</h1>
        <p className="muted">
          {opp.codigo} · <span className={`estado-badge estado-${opp.estado.toLowerCase()}`}>{estadoLabel(opp.estado)}</span>
          {" · "}{opp.dominio}
        </p>
      </header>

      {error && <p className="error" role="alert">{error}</p>}
      {msg && <p className="success" role="status">{msg}</p>}

      <section className="panel compact-panel chain-panel">
        <h2 className="section-title">Cadena operativa</h2>
        <ol className="chain-list">
          {chainSteps.map((step) => (
            <li key={step.label} className={step.done ? "done" : "pending"}>
              {step.link ? <Link to={step.link}>{step.label}</Link> : step.label}
            </li>
          ))}
        </ol>
      </section>

      <div className="toolbar compact-toolbar">
        {canEvaluate && (
          <button type="button" onClick={onEvaluar} title="Re-evaluar pertinencia y prioridad">Evaluar</button>
        )}
        {canApprove && opp.estado === "PENDIENTE_APROBACION" && (
          <>
            <button type="button" onClick={onAprobar} title="Aprobar oportunidad">Aprobar</button>
            <input
              type="text"
              placeholder="Motivo de rechazo (opcional)"
              value={rejectMotivo}
              onChange={(e) => setRejectMotivo(e.target.value)}
              className="inline-input"
            />
            <button type="button" className="btn-secondary" onClick={onRechazar} title="Rechazar oportunidad">Rechazar</button>
          </>
        )}
        {canActivate && !opp.work_plan_id && !["DESCARTADA", "CANCELADA", "MATERIALIZADA"].includes(opp.estado) && (
          <>
            <label className="inline-check">
              <input type="checkbox" checked={autoExecute} onChange={(e) => setAutoExecute(e.target.checked)} />
              Ejecutar al activar
            </label>
            <button type="button" onClick={onActivar} title="Activar y crear plan de trabajo">Activar</button>
          </>
        )}
        {canRunOps && opp.work_plan_id && planStatus === "READY" && (
          <button type="button" onClick={onRunPlan} title="Ejecutar plan de trabajo">Ejecutar plan</button>
        )}
      </div>

      <nav className="tab-bar compact-tabs">
        {TABS.map((t) => (
          <button key={t.id} type="button" className={tab === t.id ? "tab-active" : ""} onClick={() => setTab(t.id)}>
            {t.label}
          </button>
        ))}
      </nav>

      <div className="panel compact-panel">
        {tab === "resumen" && (
          <dl className="detail-grid">
            <dt>Tipo</dt><dd>{opp.tipo}</dd>
            <dt>Responsable IA</dt>
            <dd>{liderId ? <Link to={`/empleados/${liderId}`}>{String((equipo?.lider as Record<string, unknown>)?.name ?? liderId)}</Link> : "—"}</dd>
            <dt>Pertinencia</dt><dd>{opp.pertinencia ?? "—"}</dd>
            <dt>Momento</dt><dd>{opp.momento ?? "—"}</dd>
            <dt>Prioridad</dt><dd>{opp.prioridad_score != null ? Number(opp.prioridad_score).toFixed(2) : "—"}</dd>
            <dt>Valor esperado</dt><dd>{formatMoney(opp.valor_potencial)} ({opp.valor_potencial_certidumbre})</dd>
            <dt>Valor materializado</dt><dd>{formatMoney(opp.valor_materializado)}</dd>
            <dt>Confianza</dt><dd>{Number(opp.confianza).toFixed(2)}</dd>
            <dt>Descripción</dt><dd>{opp.descripcion ?? "—"}</dd>
            {accion && (
              <>
                <dt>Siguiente acción</dt>
                <dd>{String(accion.que ?? accion.tipo ?? "—")}</dd>
              </>
            )}
          </dl>
        )}

        {tab === "evidencia" && <JsonBlock value={opp.evidencia} />}

        {tab === "seguimiento" && (
          <div className="stack-gap">
            {canManage && (
              <form className="compact-form" onSubmit={onAddTracking}>
                <h3 className="section-title">Registrar seguimiento</h3>
                <label>
                  Acción
                  <input value={trackAccion} onChange={(e) => setTrackAccion(e.target.value)} required maxLength={200} />
                </label>
                <label>
                  Observación / bloqueo
                  <textarea value={trackObs} onChange={(e) => setTrackObs(e.target.value)} rows={2} />
                </label>
                <button type="submit">Guardar seguimiento</button>
              </form>
            )}
            <table className="data-table compact-table">
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Acción</th>
                  <th>Observación</th>
                  <th>Resultado</th>
                </tr>
              </thead>
              <tbody>
                {(trace?.seguimiento ?? []).length === 0 && (
                  <tr><td colSpan={4} className="muted">Sin registros de seguimiento</td></tr>
                )}
                {(trace?.seguimiento ?? []).map((row, idx) => (
                  <tr key={row.id ?? idx}>
                    <td>{formatDate(row.fecha)}</td>
                    <td>{row.accion}</td>
                    <td>{row.bloqueo ?? "—"}</td>
                    <td>{row.resultado ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {tab === "resultado" && (
          <div className="stack-gap">
            {opp.resultado ? (
              <dl className="detail-grid">
                <dt>Estado</dt><dd>{String(opp.resultado.estado ?? "—")}</dd>
                <dt>Valor real</dt><dd>{formatMoney(opp.resultado.valor_real as number | null)}</dd>
                <dt>Valor esperado</dt><dd>{formatMoney(opp.resultado.valor_esperado as number | null)}</dd>
                <dt>Fecha</dt><dd>{formatDate(opp.resultado.fecha as string)}</dd>
                <dt>Evidencia</dt><dd><JsonBlock value={opp.resultado.evidencia} /></dd>
              </dl>
            ) : (
              <p className="muted">Aún no hay resultado registrado.</p>
            )}
            {canManage && opp.estado !== "MATERIALIZADA" && opp.estado !== "DESCARTADA" && (
              <form className="compact-form" onSubmit={onRegisterResult}>
                <h3 className="section-title">Registrar resultado</h3>
                <label>
                  Valor real materializado
                  <input type="number" value={resultValor} onChange={(e) => setResultValor(e.target.value)} min={0} step={1} />
                </label>
                <label>
                  Valor esperado (opcional)
                  <input type="number" value={resultEsperado} onChange={(e) => setResultEsperado(e.target.value)} min={0} step={1} />
                </label>
                <label>
                  Evidencia (texto)
                  <textarea value={resultEvidencia} onChange={(e) => setResultEvidencia(e.target.value)} rows={2} />
                </label>
                <label>
                  Estado del resultado
                  <select value={resultEstado} onChange={(e) => setResultEstado(e.target.value)}>
                    <option value="EXITO">Éxito</option>
                    <option value="PARCIAL">Parcial</option>
                    <option value="FALLO">Fallo</option>
                  </select>
                </label>
                <button type="submit">Registrar y materializar</button>
              </form>
            )}
          </div>
        )}

        {tab === "ejecucion" && (
          <div className="stack-gap">
            {!opp.work_plan_id ? (
              <p className="muted">La oportunidad aún no tiene plan de trabajo. Actívela cuando esté aprobada.</p>
            ) : (
              <>
                <dl className="detail-grid">
                  <dt>Operación / Plan</dt>
                  <dd><Link to={`/operaciones/${opp.work_plan_id}`}>{opp.work_plan_id}</Link></dd>
                  <dt>Ejecución</dt>
                  <dd><Link to={`/ejecuciones/${opp.work_plan_id}`}>Ver ejecución</Link></dd>
                  <dt>Estado del plan</dt><dd>{planStatus ?? "—"}</dd>
                  <dt>Correlación</dt><dd>{opp.correlation_id ?? "—"}</dd>
                </dl>
                {pendingApprovals.length > 0 && (
                  <div>
                    <h3 className="section-title">Aprobaciones pendientes</h3>
                    {pendingApprovals.map((ap) => (
                      <div key={String(ap.id)} className="approval-card">
                        <p><strong>{String(ap.action ?? "Acción")}</strong></p>
                        <p className="muted">{String(ap.reason ?? "")}</p>
                        {canDecideApproval && (
                          <div className="toolbar compact-toolbar">
                            <button type="button" onClick={() => onDecideApproval(String(ap.id), "approve")}>Aprobar ejecución</button>
                            <button type="button" className="btn-secondary" onClick={() => onDecideApproval(String(ap.id), "reject")}>Rechazar</button>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {tab === "trazabilidad" && (
          <div className="stack-gap">
            <h3 className="section-title">Transiciones de estado</h3>
            <table className="data-table compact-table">
              <thead><tr><th>Fecha</th><th>De</th><th>A</th><th>Motivo</th></tr></thead>
              <tbody>
                {(trace?.transiciones ?? []).map((t, i) => (
                  <tr key={i}>
                    <td>{formatDate(t.fecha)}</td>
                    <td>{estadoLabel(t.de)}</td>
                    <td>{estadoLabel(t.a)}</td>
                    <td>{t.motivo ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <h3 className="section-title">Trazas del motor</h3>
            <table className="data-table compact-table">
              <thead><tr><th>Fecha</th><th>Etapa</th><th>Detalle</th></tr></thead>
              <tbody>
                {(trace?.trazas ?? []).map((t, i) => (
                  <tr key={i}>
                    <td>{formatDate(t.fecha)}</td>
                    <td>{t.etapa}</td>
                    <td><JsonBlock value={t.detalle} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {tab === "finops" && (
          <div>
            <dl className="detail-grid">
              <dt>Referencia FINOPS</dt><dd>{opp.finops_reference ?? "—"}</dd>
              <dt>Plan de trabajo</dt>
              <dd>{opp.work_plan_id ? <Link to={`/operaciones/${opp.work_plan_id}`}>{opp.work_plan_id}</Link> : "—"}</dd>
              <dt>Atribución</dt><dd>{opp.atribucion_nivel ?? "—"}</dd>
              <dt>Valor potencial</dt><dd>{formatMoney(opp.valor_potencial)}</dd>
              <dt>Valor materializado</dt><dd>{formatMoney(opp.valor_materializado)}</dd>
              <dt>Costo IA acumulado</dt><dd>{economics?.total_cost_label ?? "—"}</dd>
              <dt>Consumos vinculados</dt><dd>{economics?.consumption_count ?? 0}</dd>
            </dl>
            {economics && economics.consumptions.length > 0 && (
              <table className="data-table compact-table" style={{ marginTop: "1rem" }}>
                <thead>
                  <tr>
                    <th>Proveedor</th>
                    <th>Modelo</th>
                    <th>Costo</th>
                    <th>Fecha</th>
                  </tr>
                </thead>
                <tbody>
                  {economics.consumptions.map((c) => (
                    <tr key={c.id}>
                      <td>{c.provider || "—"}</td>
                      <td>{c.model_name || "—"}</td>
                      <td>{c.cost_label}</td>
                      <td className="mono">{c.created_at?.slice(0, 19)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
