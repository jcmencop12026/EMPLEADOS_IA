import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import type { OpportunityItem, ValuationSummary } from "../api";
import {
  activateOpportunity,
  approveOpportunity,
  createValuation,
  evaluateOpportunity,
  fetchOpportunity,
  fetchOpportunityEconomics,
  fetchOpportunityTrace,
  fetchValuationSummary,
  registerValuationCost,
  registerValuationReal,
  updateValuationExpected,
  updateValuationScenario,
  validateValuation,
  type FinOpsOpportunityEconomics,
} from "../api";

type Tab = "resumen" | "evidencia" | "contexto" | "accion" | "equipo" | "trazabilidad" | "finops" | "valoracion";

const TABS: { id: Tab; label: string }[] = [
  { id: "resumen", label: "Resumen" },
  { id: "evidencia", label: "Evidencia" },
  { id: "contexto", label: "Contexto" },
  { id: "accion", label: "Siguiente acción" },
  { id: "equipo", label: "Equipo IA" },
  { id: "trazabilidad", label: "Trazabilidad" },
  { id: "finops", label: "FinOps" },
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

export function OportunidadDetailPage() {
  const { opportunityId } = useParams<{ opportunityId: string }>();
  const [opp, setOpp] = useState<OpportunityItem & Record<string, unknown> | null>(null);
  const [trace, setTrace] = useState<Record<string, unknown> | null>(null);
  const [economics, setEconomics] = useState<FinOpsOpportunityEconomics | null>(null);
  const [valuation, setValuation] = useState<ValuationSummary | null>(null);
  const [tab, setTab] = useState<Tab>("resumen");
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  function reload() {
    if (!opportunityId) return;
    Promise.all([
      fetchOpportunity(opportunityId),
      fetchOpportunityTrace(opportunityId),
      fetchOpportunityEconomics(opportunityId).catch(() => null),
      fetchValuationSummary(opportunityId).catch(() => null),
    ])
      .then(([o, t, eco, val]) => {
        setOpp(o as OpportunityItem & Record<string, unknown>);
        setTrace(t);
        setEconomics(eco);
        setValuation(val);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Error"));
  }

  useEffect(() => { reload(); }, [opportunityId]);

  async function onEvaluar() {
    if (!opportunityId) return;
    try {
      await evaluateOpportunity(opportunityId);
      setMsg("Evaluación completada");
      reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    }
  }

  async function onAprobar() {
    if (!opportunityId) return;
    try {
      await approveOpportunity(opportunityId, true, "Aprobación desde centro");
      setMsg("Oportunidad aprobada");
      reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    }
  }

  async function onActivar() {
    if (!opportunityId) return;
    try {
      await activateOpportunity(opportunityId);
      setMsg("Oportunidad activada — WorkPlan creado");
      reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
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
      reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    }
  }

  async function onGuardarEsperado() {
    if (!opportunityId) return;
    const gross = prompt("Valor bruto esperado:");
    const prob = prompt("Probabilidad (0-1):");
    if (!gross || !prob) return;
    try {
      await updateValuationExpected(opportunityId, {
        gross_value: gross,
        probability: prob,
        period_days: 90,
        value_nature: "ESTIMADA",
        assumptions: "Estimación inicial",
        source: "Usuario",
      });
      setMsg("Valor esperado actualizado");
      reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    }
  }

  async function onGuardarEscenario(tipo: string) {
    if (!opportunityId) return;
    const valor = prompt(`Valor escenario ${tipo}:`);
    const prob = prompt("Probabilidad (0-1):");
    if (!valor || !prob) return;
    try {
      await updateValuationScenario(opportunityId, tipo, {
        value_amount: valor,
        probability: prob,
        assumptions: `Escenario ${tipo}`,
      });
      setMsg(`Escenario ${tipo} actualizado`);
      reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    }
  }

  async function onRegistrarReal() {
    if (!opportunityId) return;
    const valor = prompt("Valor materializado:");
    if (!valor) return;
    try {
      await registerValuationReal(opportunityId, {
        materialized_value: valor,
        value_nature: "VERIFICADO",
        attribution_level: "ATRIBUIBLE",
        source: "Medición interna",
        evidence: "Registro manual",
      });
      setMsg("Valor real registrado");
      reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    }
  }

  async function onRegistrarCosto() {
    if (!opportunityId) return;
    const monto = prompt("Monto del costo:");
    if (!monto) return;
    try {
      await registerValuationCost(opportunityId, {
        cost_type: "HORAS HUMANAS",
        amount: monto,
        currency: "USD",
        description: "Costo de ejecución",
      });
      setMsg("Costo registrado");
      reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    }
  }

  async function onValidar() {
    if (!opportunityId) return;
    try {
      await validateValuation(opportunityId);
      setMsg("Valoración validada");
      reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    }
  }

  if (!opp) return <div className="ops-page"><p className="muted">Cargando…</p></div>;

  const accion = opp.siguiente_accion as Record<string, unknown> | null;
  const equipo = opp.equipo as Record<string, unknown> | null;

  return (
    <div className="ops-page">
      <header className="page-header">
        <p><Link to="/oportunidades">← Centro de oportunidades</Link></p>
        <h1>{opp.titulo as string}</h1>
        <p className="muted">{opp.codigo as string} · {opp.estado as string} · {opp.dominio as string}</p>
      </header>

      {error && <p className="error">{error}</p>}
      {msg && <p className="success">{msg}</p>}

      <div className="toolbar" style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
        <button type="button" onClick={onEvaluar} title="Re-evaluar pertinencia y prioridad">Evaluar</button>
        <button type="button" onClick={onAprobar} title="Aprobar oportunidad">Aprobar</button>
        <button type="button" onClick={onActivar} title="Activar y crear WorkPlan">Activar</button>
      </div>

      <nav className="tab-bar" style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem", flexWrap: "wrap" }}>
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            className={tab === t.id ? "tab-active" : ""}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <div className="panel">
        {tab === "resumen" && (
          <dl className="detail-grid">
            <dt>Tipo</dt><dd>{opp.tipo as string}</dd>
            <dt>Pertinencia</dt><dd>{opp.pertinencia as string ?? "—"}</dd>
            <dt>Momento</dt><dd>{opp.momento as string ?? "—"}</dd>
            <dt>Prioridad</dt><dd>{opp.prioridad_score != null ? Number(opp.prioridad_score).toFixed(2) : "—"}</dd>
            <dt>Valor potencial</dt><dd>{opp.valor_potencial as number ?? "—"} ({opp.valor_potencial_certidumbre as string})</dd>
            <dt>Valor materializado</dt><dd>{opp.valor_materializado as number ?? "—"}</dd>
            <dt>Confianza</dt><dd>{Number(opp.confianza).toFixed(2)}</dd>
            <dt>Descripción</dt><dd>{(opp.descripcion as string) ?? "—"}</dd>
          </dl>
        )}
        {tab === "evidencia" && (
          <pre>{JSON.stringify(opp.evidencia, null, 2)}</pre>
        )}
        {tab === "contexto" && (
          <pre>{JSON.stringify(opp.contexto, null, 2)}</pre>
        )}
        {tab === "accion" && (
          accion ? <pre>{JSON.stringify(accion, null, 2)}</pre> : <p className="muted">Sin acción definida</p>
        )}
        {tab === "equipo" && (
          equipo ? <pre>{JSON.stringify(equipo, null, 2)}</pre> : <p className="muted">Equipo no asignado</p>
        )}
        {tab === "trazabilidad" && (
          <pre>{JSON.stringify(trace, null, 2)}</pre>
        )}
        {tab === "finops" && (
          <div>
            <dl className="detail-grid">
              <dt>Referencia FINOPS</dt><dd>{(opp.finops_reference as string) ?? "—"}</dd>
              <dt>WorkPlan</dt><dd>{(opp.work_plan_id as string) ?? "—"}</dd>
              <dt>Atribución</dt><dd>{(opp.atribucion_nivel as string) ?? "—"}</dd>
              <dt>Costo IA acumulado</dt><dd>{economics?.total_cost_label ?? "—"}</dd>
              <dt>Consumos vinculados</dt><dd>{economics?.consumption_count ?? 0}</dd>
            </dl>
            {economics && economics.consumptions.length > 0 && (
              <table className="data-table" style={{ marginTop: "1rem" }}>
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
          <div>
            {!valuation?.has_valuation ? (
              <div>
                <p className="muted">Sin valoración económica registrada.</p>
                <button type="button" onClick={onCrearValoracion}>Crear valoración</button>
              </div>
            ) : (
              <>
                <div className="toolbar" style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginBottom: "1rem" }}>
                  <button type="button" onClick={onGuardarEsperado}>Valor esperado</button>
                  <button type="button" onClick={() => onGuardarEscenario("CONSERVADOR")}>Esc. conservador</button>
                  <button type="button" onClick={() => onGuardarEscenario("BASE")}>Esc. base</button>
                  <button type="button" onClick={() => onGuardarEscenario("OPTIMISTA")}>Esc. optimista</button>
                  <button type="button" onClick={onRegistrarReal}>Valor real</button>
                  <button type="button" onClick={onRegistrarCosto}>Costo ejecución</button>
                  <button type="button" onClick={onValidar}>Validar</button>
                </div>

                <dl className="detail-grid">
                  <dt>Tipo de valor</dt>
                  <dd>{valuation.valuation?.value_type} ({valuation.valuation?.scope})</dd>
                  <dt>Estado</dt><dd>{valuation.valuation?.status} · v{valuation.valuation?.version}</dd>
                  <dt className="highlight-esperado">Valor esperado ajustado</dt>
                  <dd>{valuation.adjusted_expected ?? "—"} <span className="badge">ESPERADO</span></dd>
                  <dt>Valor bruto esperado</dt><dd>{valuation.gross_expected ?? "—"}</dd>
                  <dt className="highlight-real">Valor materializado</dt>
                  <dd>{valuation.materialized_value ?? "—"} <span className="badge">REAL</span></dd>
                  <dt>Valor atribuible</dt>
                  <dd>
                    {valuation.attributable_value ?? "—"}
                    {valuation.real?.value_nature && (
                      <span className="badge"> {valuation.real.value_nature}</span>
                    )}
                  </dd>
                  <dt>Costo total ejecución</dt>
                  <dd>{valuation.total_execution_cost ?? "—"} (IA: {valuation.finops_ia_cost_label})</dd>
                  <dt>Beneficio neto</dt><dd>{valuation.net_benefit ?? "—"}</dd>
                  <dt>Retorno</dt><dd>{valuation.return_label ?? "NO CALCULABLE"}</dd>
                  <dt>Periodo recuperación</dt><dd>{valuation.payback_label ?? "NO CALCULABLE"}</dd>
                  <dt>Atribución</dt>
                  <dd>{valuation.real?.attribution_level ?? "—"}</dd>
                </dl>

                {valuation.missing_for_calculation && valuation.missing_for_calculation.length > 0 && (
                  <p className="muted" style={{ marginTop: "0.5rem" }}>
                    Datos faltantes: {valuation.missing_for_calculation.join("; ")}
                  </p>
                )}

                {valuation.scenarios && valuation.scenarios.length > 0 && (
                  <table className="data-table" style={{ marginTop: "1rem" }}>
                    <thead>
                      <tr>
                        <th>Escenario</th>
                        <th>Valor</th>
                        <th>Prob.</th>
                        <th>Ajustado</th>
                        <th>Costo</th>
                      </tr>
                    </thead>
                    <tbody>
                      {valuation.scenarios.map((s) => (
                        <tr key={s.scenario_type}>
                          <td>{s.scenario_type}</td>
                          <td>{s.value_amount ?? "—"}</td>
                          <td>{s.probability ?? "—"}</td>
                          <td>{s.adjusted_value ?? "—"}</td>
                          <td>{s.cost ?? "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}

                {valuation.history && valuation.history.length > 0 && (
                  <details style={{ marginTop: "1rem" }}>
                    <summary>Histórico ({valuation.history.length})</summary>
                    <ul>
                      {valuation.history.map((h, i) => (
                        <li key={i} className="mono">
                          v{h.version} · {h.action} · {h.change_summary ?? ""} · {h.changed_at?.slice(0, 19)}
                        </li>
                      ))}
                    </ul>
                  </details>
                )}

                <p className="muted" style={{ marginTop: "0.75rem", fontSize: "0.85rem" }}>
                  Tipos disponibles: {VALUE_TYPES.join(", ")}
                </p>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
