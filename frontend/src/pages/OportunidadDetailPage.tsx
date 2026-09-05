import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import type { OpportunityItem, OpportunityTrace, ValuationSummary } from "../api";
import {
  activateOpportunity,
  addOpportunityTracking,
  approveOpportunity,
  createValuation,
  decideApproval,
  evaluateOpportunity,
  fetchExecution,
  fetchOperationApprovals,
  fetchOpportunity,
  fetchOpportunityEconomics,
  fetchOpportunityTrace,
  fetchValuationSummary,
  registerOpportunityResult,
  registerValuationCost,
  registerValuationReal,
  runOperation,
  updateValuationExpected,
  updateValuationScenario,
  validateValuation,
  type FinOpsOpportunityEconomics,
} from "../api";
import { usePermissions } from "../hooks/usePermissions";
import { usePageAssistantContext } from "../hooks/usePageAssistantContext";
import { formatCalcLabel } from "../lib/uiTerms";
import { label as labelExec } from "../lib/labels";
import { EXECUTION_STATUS } from "../lib/labels";
import {
  formatConfianza,
  formatPrioridad,
  formatValorConCertidumbre,
  formatTraceDetalle,
  labelEstadoOportunidad,
  labelMomento,
  labelPertinencia,
  labelTipoOportunidad,
  labelTraceEtapa,
  RESULTADO_OPORTUNIDAD,
  labelOportunidad,
  SCENARIO_TYPE,
} from "../lib/oportunidadLabels";
import { StructuredEvidenceView } from "../components/StructuredEvidenceView";
import { ValuationFormsPanel } from "../components/oportunidad/ValuationFormsPanel";
import { OpportunityProgress, opportunityStepFromEstado, PageHeader, StatusBadge, EmptyState, FormSection, TechnicalDetails } from "../components/v1";

type Tab = "resumen" | "evidencia" | "seguimiento" | "resultado" | "ejecucion" | "trazabilidad" | "finops" | "valoracion";

const TABS: { id: Tab; label: string }[] = [
  { id: "resumen", label: "Resumen" },
  { id: "evidencia", label: "Evidencia" },
  { id: "seguimiento", label: "Seguimiento" },
  { id: "resultado", label: "Resultado" },
  { id: "ejecucion", label: "Ejecución" },
  { id: "trazabilidad", label: "Trazabilidad" },
  { id: "finops", label: "Costos y consumo" },
  { id: "valoracion", label: "Valoración" },
];

const VALUE_TYPES = [
  "AHORRO",
  "PÉRDIDA EVITADA",
  "INGRESO RECUPERADO",
  "PRODUCTIVIDAD LIBERADA",
  "NUEVO INGRESO",
  "OPORTUNIDAD COMERCIAL",
  "RIESGO MITIGADO",
  "OTRO",
];

const VALUATION_ACTION_LABELS: Record<string, string> = {
  CREATE: "Creación",
  UPDATE_EXPECTED: "Actualización valor esperado",
  UPDATE_SCENARIO: "Actualización escenario",
  REGISTER_REAL: "Registro valor real",
  REGISTER_COST: "Registro costo",
  VALIDATE: "Validación",
};

function labelValuationAction(action: string): string {
  return VALUATION_ACTION_LABELS[action] ?? action.replace(/_/g, " ").toLowerCase();
}

function formatMoney(v: number | null | undefined): string {
  if (v == null) return "—";
  return new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(v);
}

function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  return new Date(value).toLocaleString("es-CO");
}

export function OportunidadDetailPage() {
  const { opportunityId } = useParams<{ opportunityId: string }>();
  const { has, loading: permsLoading } = usePermissions();
  const [opp, setOpp] = useState<OpportunityItem | null>(null);
  const [trace, setTrace] = useState<OpportunityTrace | null>(null);
  const [economics, setEconomics] = useState<FinOpsOpportunityEconomics | null>(null);
  const [valuation, setValuation] = useState<ValuationSummary | null>(null);
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
  const canValManage = has("valoracion.manage");
  const canValValidate = has("valoracion.validate");

  usePageAssistantContext(
    {
      oportunidad_id: opportunityId,
      tab,
      titulo: opp?.titulo,
      estado: opp?.estado,
      valor_potencial: opp?.valor_potencial,
    },
    Boolean(opportunityId),
  );

  async function reload() {
    if (!opportunityId) return;
    setLoading(true);
    setError(null);
    try {
      const [o, t, eco, val] = await Promise.all([
        fetchOpportunity(opportunityId),
        fetchOpportunityTrace(opportunityId),
        fetchOpportunityEconomics(opportunityId).catch(() => null),
        fetchValuationSummary(opportunityId).catch(() => null),
      ]);
      setOpp(o);
      setTrace(t);
      setEconomics(eco);
      setValuation(val);
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
      setMsg(autoExecute ? "Oportunidad activada y ejecución iniciada" : "Oportunidad activada — plan de trabajo creado");
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

  async function onCrearValoracion() {
    if (!opportunityId) return;
    try {
      await createValuation(opportunityId, {
        value_type: "AHORRO",
        scope: "INTERNO",
        currency: "USD",
      });
      setMsg("Valoración creada");
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al crear valoración");
    }
  }

  async function onGuardarEsperado(data: { gross_value: string; probability: string; assumptions: string }) {
    if (!opportunityId) return;
    try {
      await updateValuationExpected(opportunityId, {
        gross_value: data.gross_value,
        probability: data.probability,
        period_days: 90,
        value_nature: "ESTIMADA",
        assumptions: data.assumptions || "Estimación inicial",
        source: "Usuario",
      });
      setMsg("Valor esperado actualizado");
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al actualizar valor esperado");
    }
  }

  async function onGuardarEscenario(tipo: string, data: { value_amount: string; probability: string; assumptions: string }) {
    if (!opportunityId) return;
    try {
      await updateValuationScenario(opportunityId, tipo, {
        value_amount: data.value_amount,
        probability: data.probability,
        assumptions: data.assumptions || `Escenario ${tipo}`,
      });
      setMsg(`Escenario ${tipo} actualizado`);
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al actualizar escenario");
    }
  }

  async function onRegistrarReal(data: { materialized_value: string; evidence: string }) {
    if (!opportunityId) return;
    try {
      await registerValuationReal(opportunityId, {
        materialized_value: data.materialized_value,
        value_nature: "VERIFICADO",
        attribution_level: "ATRIBUIBLE",
        source: "Medición interna",
        evidence: data.evidence,
      });
      setMsg("Valor real registrado");
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al registrar valor real");
    }
  }

  async function onRegistrarCosto(data: { amount: string; description: string }) {
    if (!opportunityId) return;
    try {
      await registerValuationCost(opportunityId, {
        cost_type: "HORAS HUMANAS",
        amount: data.amount,
        currency: "USD",
        description: data.description || "Costo de ejecución",
      });
      setMsg("Costo registrado");
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al registrar costo");
    }
  }

  async function onValidar() {
    if (!opportunityId) return;
    try {
      await validateValuation(opportunityId);
      setMsg("Valoración validada");
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al validar valoración");
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
      <p className="muted small"><Link to="/oportunidades">← Centro de oportunidades</Link></p>
      <PageHeader
        title={opp.titulo}
        subtitle={`${opp.codigo} · ${opp.dominio}`}
        actions={<StatusBadge label={labelEstadoOportunidad(opp.estado)} tone="info" />}
      />

      {error && <p className="error" role="alert">{error}</p>}
      {msg && <p className="success" role="status">{msg}</p>}

      <section className="panel compact-panel">
        <h2 className="section-title">Progreso de la oportunidad</h2>
        <OpportunityProgress currentStep={opportunityStepFromEstado(opp.estado)} />
      </section>

      <div className="toolbar compact-toolbar v1-opp-actions">
        {canEvaluate && (
          <button type="button" className="btn secondary" onClick={onEvaluar} title="Re-evaluar pertinencia y prioridad">Evaluar</button>
        )}
        {canApprove && opp.estado === "PENDIENTE_APROBACION" && (
          <>
            <button type="button" className="btn primary" onClick={onAprobar} title="Aprobar oportunidad">Aprobar</button>
            <input
              type="text"
              placeholder="Motivo de rechazo (opcional)"
              value={rejectMotivo}
              onChange={(e) => setRejectMotivo(e.target.value)}
              className="inline-input"
            />
            <button type="button" className="btn secondary" onClick={onRechazar} title="Rechazar oportunidad">Rechazar</button>
          </>
        )}
        {canActivate && !opp.work_plan_id && !["DESCARTADA", "CANCELADA", "MATERIALIZADA"].includes(opp.estado) && (
          <>
            <label className="inline-check">
              <input type="checkbox" checked={autoExecute} onChange={(e) => setAutoExecute(e.target.checked)} />
              Ejecutar al activar
            </label>
            <button type="button" className="btn primary" onClick={onActivar} title="Activar y crear plan de trabajo">Activar</button>
          </>
        )}
        {canRunOps && opp.work_plan_id && planStatus === "READY" && (
          <button type="button" className="btn primary" onClick={onRunPlan} title="Ejecutar plan de trabajo">Ejecutar plan</button>
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
            <dt>Tipo</dt><dd>{labelTipoOportunidad(opp.tipo)}</dd>
            <dt>Responsable IA</dt>
            <dd>{liderId ? <Link to={`/empleados/${liderId}`}>{String((equipo?.lider as Record<string, unknown>)?.name ?? "Responsable asignado")}</Link> : "Sin responsable asignado"}</dd>
            <dt>Pertinencia</dt><dd>{labelPertinencia(opp.pertinencia)}</dd>
            <dt>Momento</dt><dd>{labelMomento(opp.momento)}</dd>
            <dt>Prioridad</dt><dd>{formatPrioridad(opp.prioridad_score != null ? Number(opp.prioridad_score) : null)}</dd>
            <dt>Valor esperado</dt><dd>{formatValorConCertidumbre(opp.valor_potencial, opp.valor_potencial_certidumbre, formatMoney)}</dd>
            <dt>Valor materializado</dt><dd>{formatMoney(opp.valor_materializado)}</dd>
            <dt>Confianza</dt><dd>{formatConfianza(Number(opp.confianza))}</dd>
            <dt>Descripción</dt><dd>{opp.descripcion ?? "—"}</dd>
            {accion && (
              <>
                <dt>Siguiente acción</dt>
                <dd>{String(accion.que ?? accion.tipo ?? "—")}</dd>
              </>
            )}
          </dl>
        )}

        {tab === "evidencia" && <StructuredEvidenceView value={opp.evidencia} title="Evidencia de la oportunidad" />}

        {tab === "seguimiento" && (
          <div className="stack-gap">
            {canManage && (
              <FormSection title="Registrar seguimiento" description="Acciones, bloqueos y resultados intermedios">
                <form className="compact-form" onSubmit={onAddTracking}>
                  <label>
                    Acción
                    <input value={trackAccion} onChange={(e) => setTrackAccion(e.target.value)} required maxLength={200} />
                  </label>
                  <label>
                    Observación / bloqueo
                    <textarea value={trackObs} onChange={(e) => setTrackObs(e.target.value)} rows={2} />
                  </label>
                  <button type="submit" className="btn primary">Guardar seguimiento</button>
                </form>
              </FormSection>
            )}
            {(trace?.seguimiento ?? []).length === 0 ? (
              <EmptyState
                title="Sin registros de seguimiento"
                description="Aún no hay seguimientos registrados. Documente acciones y bloqueos para mantener trazabilidad operativa."
                action={
                  canManage ? undefined : (
                    <p className="muted small">Solicite a un responsable con permisos de gestión que registre el primer seguimiento.</p>
                  )
                }
              />
            ) : (
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
            )}
          </div>
        )}

        {tab === "resultado" && (
          <div className="stack-gap">
            {opp.resultado ? (
              <dl className="detail-grid">
                <dt>Estado</dt><dd>{labelOportunidad(RESULTADO_OPORTUNIDAD, String(opp.resultado.estado ?? ""))}</dd>
                <dt>Valor real</dt><dd>{formatMoney(opp.resultado.valor_real as number | null)}</dd>
                <dt>Valor esperado</dt><dd>{formatMoney(opp.resultado.valor_esperado as number | null)}</dd>
                <dt>Fecha</dt><dd>{formatDate(opp.resultado.fecha as string)}</dd>
                <dt>Evidencia</dt><dd><StructuredEvidenceView value={opp.resultado.evidencia} /></dd>
              </dl>
            ) : (
              <EmptyState
                title="Aún no hay resultado registrado"
                description="Registre el valor real materializado, la evidencia y el estado cuando la oportunidad haya generado impacto medible."
              />
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
              <EmptyState
                title="Ejecución pendiente de plan de trabajo"
                description={
                  opp.estado === "PENDIENTE_APROBACION" || opp.estado === "DETECTADA"
                    ? "La oportunidad debe evaluarse, aprobarse y activarse antes de crear un plan de trabajo."
                    : "Un responsable de operaciones debe crear el plan y asignar la ejecución tras la activación."
                }
                action={
                  canApprove && opp.estado === "PENDIENTE_APROBACION" ? (
                    <button type="button" className="btn primary" onClick={() => void onAprobar()}>Aprobar oportunidad</button>
                  ) : canActivate && opp.estado === "APROBADA" ? (
                    <button type="button" className="btn primary" onClick={() => void onActivar()}>Activar oportunidad</button>
                  ) : undefined
                }
              />
            ) : (
              <>
                <dl className="detail-grid">
                  <dt>Operación / Plan</dt>
                  <dd><Link to={`/operaciones/${opp.work_plan_id}`}>Ver plan de trabajo</Link></dd>
                  <dt>Ejecución</dt>
                  <dd><Link to={`/ejecuciones/${opp.work_plan_id}`}>Ver ejecución</Link></dd>
                  <dt>Estado del plan</dt><dd>{labelExec(EXECUTION_STATUS, planStatus)}</dd>
                </dl>
                <TechnicalDetails title="Ver detalle técnico">
                  <p className="mono small">Plan ID: {opp.work_plan_id}</p>
                  <p className="mono small">Correlación: {opp.correlation_id ?? "—"}</p>
                </TechnicalDetails>
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
            <h3 className="section-title">Historial empresarial</h3>
            <table className="data-table compact-table">
              <thead><tr><th>Fecha</th><th>Evento</th><th>Cambio</th><th>Motivo</th></tr></thead>
              <tbody>
                {(trace?.transiciones ?? []).length === 0 && (
                  <tr><td colSpan={4} className="muted">Sin transiciones registradas</td></tr>
                )}
                {(trace?.transiciones ?? []).map((t, i) => (
                  <tr key={i}>
                    <td>{formatDate(t.fecha)}</td>
                    <td>{labelEstadoOportunidad(t.a)}</td>
                    <td>{labelEstadoOportunidad(t.de)} → {labelEstadoOportunidad(t.a)}</td>
                    <td>{t.motivo ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <h3 className="section-title">Eventos del motor</h3>
            <table className="data-table compact-table">
              <thead><tr><th>Fecha</th><th>Evento</th><th>Detalle</th></tr></thead>
              <tbody>
                {(trace?.trazas ?? []).length === 0 && (
                  <tr><td colSpan={3} className="muted">Sin eventos adicionales</td></tr>
                )}
                {(trace?.trazas ?? []).map((t, i) => (
                  <tr key={i}>
                    <td>{formatDate(t.fecha)}</td>
                    <td>{labelTraceEtapa(t.etapa)}</td>
                    <td>{formatTraceDetalle(t.detalle)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {tab === "finops" && (
          <div>
            <dl className="detail-grid">
              <dt>Valor potencial</dt><dd>{formatMoney(opp.valor_potencial)}</dd>
              <dt>Valor materializado</dt><dd>{formatMoney(opp.valor_materializado)}</dd>
              <dt>Costo IA acumulado</dt><dd>{economics?.total_cost_label ?? "—"}</dd>
              <dt>Consumos vinculados</dt><dd>{economics?.consumption_count ?? 0}</dd>
            </dl>
            {!economics?.total_cost_label && (
              <p className="muted small">
                El costo de ejecución puede no estar disponible hasta que existan consumos IA atribuibles a esta oportunidad.
              </p>
            )}
            <TechnicalDetails title="Ver detalle técnico">
              <dl className="detail-grid compact">
                <dt>Referencia de costos</dt><dd className="mono">{opp.finops_reference ?? "—"}</dd>
                <dt>Plan de trabajo</dt><dd className="mono">{opp.work_plan_id ?? "—"}</dd>
                <dt>Atribución</dt><dd>{opp.atribucion_nivel ?? "—"}</dd>
              </dl>
            </TechnicalDetails>
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

        {tab === "valoracion" && (
          <div className="stack-gap">
            <ValuationFormsPanel
              valuation={valuation}
              canManage={canValManage}
              canValidate={canValValidate}
              onCreate={onCrearValoracion}
              onExpected={onGuardarEsperado}
              onScenario={onGuardarEscenario}
              onReal={onRegistrarReal}
              onCost={onRegistrarCosto}
              onValidate={onValidar}
            />
            {valuation?.has_valuation && (
              <>
                <dl className="detail-grid">
                  <dt>Beneficio neto</dt><dd>{valuation.net_benefit ?? "—"}</dd>
                  <dt>Retorno</dt><dd>{formatCalcLabel(valuation.return_label)}</dd>
                  <dt>Periodo recuperación</dt><dd>{formatCalcLabel(valuation.payback_label)}</dd>
                  <dt>Atribución</dt>
                  <dd>{valuation.real?.attribution_level ?? "—"}</dd>
                </dl>
                {valuation.missing_for_calculation && valuation.missing_for_calculation.length > 0 && (
                  <p className="muted">Para completar el cálculo faltan: {valuation.missing_for_calculation.join("; ")}</p>
                )}
                {valuation.scenarios && valuation.scenarios.length > 0 && (
                  <table className="data-table compact-table">
                    <thead>
                      <tr><th>Escenario</th><th>Valor</th><th>Prob.</th><th>Ajustado</th><th>Costo</th></tr>
                    </thead>
                    <tbody>
                      {valuation.scenarios.map((s) => (
                        <tr key={s.scenario_type}>
                          <td>{labelOportunidad(SCENARIO_TYPE, s.scenario_type)}</td>
                          <td className="num">{s.value_amount ?? "—"}</td>
                          <td className="num">{s.probability ?? "—"}</td>
                          <td className="num">{s.adjusted_value ?? "—"}</td>
                          <td className="num">{s.cost ?? "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
                {valuation.history && valuation.history.length > 0 && (
                  <details>
                    <summary>Histórico de valoración ({valuation.history.length})</summary>
                    <ul className="cc-list-compact">
                      {valuation.history.map((h, i) => (
                        <li key={i}>
                          v{h.version} · {labelValuationAction(String(h.action))} · {h.change_summary ?? ""} · {h.changed_at?.slice(0, 19)}
                        </li>
                      ))}
                    </ul>
                  </details>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
