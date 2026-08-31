import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  addCommercialCost,
  addCommercialScenario,
  addCommercialValue,
  approveCommercialProposal,
  detectCommercialDoubleCount,
  fetchCommercialProposal,
  fetchCommercialTraceability,
  setCommercialFinalPrice,
  simulateCommercialProposal,
  suggestCommercialPrice,
  type CommercialProposalDetail,
} from "../api";
import { CredentialModeBadge } from "../components/comercial/CredentialModeBadge";
import { HelpTooltip } from "../components/comercial/HelpTooltip";
import { ValueNatureCards } from "../components/comercial/ValueNatureCards";
import {
  extractNatureBreakdown,
  formatMoney,
  formatPct,
  TOOLTIPS,
  VALUE_CATEGORY_LABELS,
} from "../lib/comercialLabels";
import { usePermissions } from "../hooks/usePermissions";

type Tab = "resumen" | "valor" | "costos" | "precio" | "trazabilidad";

export function ComercialPropuestaDetailPage() {
  const { proposalId } = useParams<{ proposalId: string }>();
  const { has } = usePermissions();
  const [detail, setDetail] = useState<CommercialProposalDetail | null>(null);
  const [trace, setTrace] = useState<Record<string, unknown> | null>(null);
  const [tab, setTab] = useState<Tab>("resumen");
  const [error, setError] = useState<string | null>(null);
  const [precioFinal, setPrecioFinal] = useState("");
  const [justificacion, setJustificacion] = useState("");
  const [simResult, setSimResult] = useState<Record<string, unknown> | null>(null);

  async function reload() {
    if (!proposalId) return;
    const [d, t] = await Promise.all([
      fetchCommercialProposal(proposalId),
      fetchCommercialTraceability(proposalId).catch(() => null),
    ]);
    setDetail(d);
    setTrace(t);
  }

  useEffect(() => {
    reload().catch((e) => setError(e instanceof Error ? e.message : "Error"));
  }, [proposalId]);

  const breakdown = useMemo(() => {
    const fromDetail = extractNatureBreakdown(detail?.desglose_naturaleza as Record<string, unknown> | undefined);
    const fromTrace = extractNatureBreakdown(trace ?? undefined);
    return Object.keys(fromDetail).length ? fromDetail : fromTrace;
  }, [detail, trace]);

  const currency = detail?.currency ?? "USD";

  async function onSuggest() {
    if (!proposalId) return;
    await suggestCommercialPrice(proposalId);
    await reload();
  }

  if (!detail) return <p>Cargando propuesta…</p>;

  const tabs: { id: Tab; label: string }[] = [
    { id: "resumen", label: "Resumen" },
    { id: "valor", label: "Valor" },
    { id: "costos", label: "Costos IA" },
    { id: "precio", label: "Precio y ROI" },
    { id: "trazabilidad", label: "Seguimiento" },
  ];

  return (
    <div className="ops-page">
      <header className="ops-header">
        <Link to="/comercial">← Comercial</Link>
        <h1>{detail.codigo} — {detail.titulo}</h1>
        <p className="muted">
          Estado: {detail.estado} · Escenario: {detail.escenario_recomendado}
          {detail.vigencia_hasta && ` · Vigencia: ${detail.vigencia_hasta.slice(0, 10)}`}
        </p>
        <CredentialModeBadge mode={detail.credential_mode ?? detail.plan?.credential_mode} />
      </header>
      {error && <p className="error-text">{error}</p>}

      <nav className="tab-nav compact-tabs">
        {tabs.map((t) => (
          <button key={t.id} type="button" className={tab === t.id ? "active" : ""} onClick={() => setTab(t.id)}>
            {t.label}
          </button>
        ))}
      </nav>

      {tab === "resumen" && (
        <>
          <ValueNatureCards breakdown={breakdown} currency={currency} />
          <section className="panel compact-panel">
            <div className="metrics-grid compact-metrics">
              <div>
                <strong>Inversión (precio sugerido)</strong>
                <span>{formatMoney(detail.precio_sugerido, currency)}</span>
              </div>
              <div>
                <strong>Beneficio neto cliente</strong>
                <span>{formatMoney(detail.beneficio_neto_cliente, currency)}</span>
              </div>
              <div>
                <strong>ROI</strong>
                <span>{formatPct(detail.roi_pct ?? null)}</span>
                <HelpTooltip text={TOOLTIPS.roi} />
              </div>
              <div>
                <strong>Payback</strong>
                <span>{detail.payback_meses != null ? `${detail.payback_meses} meses` : "—"}</span>
                <HelpTooltip text={TOOLTIPS.payback} />
              </div>
              {detail.plan && (
                <div>
                  <strong>Plan</strong>
                  <span>
                    <Link to={`/comercial/planes/${detail.plan.id}`}>{detail.plan.name}</Link>
                  </span>
                </div>
              )}
            </div>
          </section>
        </>
      )}

      {tab === "valor" && (
        <section className="panel compact-panel">
          <h2>Desglose por naturaleza</h2>
          <ValueNatureCards breakdown={breakdown} currency={currency} />
          <h3>Componentes de valor</h3>
          <table className="data-table compact-table">
            <thead>
              <tr>
                <th>Categoría</th>
                <th>Naturaleza</th>
                <th>Alcance</th>
                <th>Bruto</th>
                <th>Atribución</th>
                <th>Atribuible</th>
              </tr>
            </thead>
            <tbody>
              {detail.valores.length === 0 && (
                <tr><td colSpan={6} className="muted">Sin componentes registrados.</td></tr>
              )}
              {detail.valores.map((v) => (
                <tr key={v.id} className={v.naturaleza === "POTENCIAL" ? "row-potential" : ""}>
                  <td>{VALUE_CATEGORY_LABELS[v.categoria] ?? v.categoria}</td>
                  <td>{v.naturaleza}</td>
                  <td>{v.alcance ?? "INTERNO"}</td>
                  <td>{formatMoney(v.valor_bruto, currency)}</td>
                  <td>{v.atribucion_pct}%</td>
                  <td>{formatMoney(v.valor_atribuible, currency)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {has("comercial.create") && (
            <button type="button" className="btn" onClick={async () => {
              if (!proposalId) return;
              await addCommercialValue(proposalId, {
                categoria: "AHORRO", naturaleza: "ESTIMADO", valor_bruto: 100000,
                atribucion_pct: 35, criterio_atribucion: "Automatización medible",
              });
              await reload();
            }}>Agregar valor ejemplo</button>
          )}
        </section>
      )}

      {tab === "costos" && (
        <section className="panel compact-panel">
          <h2>Costos de la propuesta</h2>
          <table className="data-table compact-table">
            <thead>
              <tr><th>Categoría</th><th>Clase</th><th>Monto</th><th>FinOps</th></tr>
            </thead>
            <tbody>
              {detail.costos.map((c) => (
                <tr key={c.id}>
                  <td>{c.categoria}</td>
                  <td>{c.clase_costo}</td>
                  <td>{formatMoney(c.monto, currency)}</td>
                  <td className="mono">{c.finops_record_id?.slice(0, 8) ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="muted">Costo total EMPLEADOS IA: {formatMoney(detail.costo_total, currency)}</p>
          {has("finops.view") && <Link to="/costos-valor">Ver consumo FinOps detallado →</Link>}
          {has("comercial.create") && (
            <button type="button" className="btn" onClick={async () => {
              if (!proposalId) return;
              await addCommercialCost(proposalId, { categoria: "CONSUMO_IA", clase_costo: "COSTO_PROVEEDOR_IA", monto: 5000 });
              await reload();
            }}>Agregar costo IA ejemplo</button>
          )}
        </section>
      )}

      {tab === "precio" && (
        <section className="panel compact-panel">
          <h2>Precio sugerido y retorno</h2>
          <div className="notice-banner subtle">
            El precio se calcula solo con valor <strong>verificado + estimado</strong>. El potencial queda excluido.
          </div>
          <div className="metrics-grid compact-metrics">
            <div><strong>Valor base precio</strong><span>{formatMoney(breakdown.valor_atribuible_precio ?? detail.valor_atribuible_total, currency)}</span></div>
            <div><strong>Precio sugerido</strong><span>{formatMoney(detail.precio_sugerido, currency)}</span></div>
            <div><strong>Precio final</strong><span>{formatMoney(detail.precio_final, currency)}</span></div>
            <div><strong>% valor capturado</strong><span>{formatPct(detail.pct_valor_capturado_empleados_ia ?? null)}</span></div>
            <div><strong>% valor conservado cliente</strong><span>{formatPct(detail.pct_valor_conservado_cliente ?? null)}</span></div>
            {has("comercial.view") && detail.margen_pct != null && (
              <div><strong>Margen</strong><span>{formatPct(detail.margen_pct)}</span></div>
            )}
          </div>
          <div className="ops-actions">
            {has("comercial.simulate") && <button type="button" className="btn primary" onClick={onSuggest}>Calcular precio sugerido</button>}
            {has("comercial.simulate") && (
              <button type="button" className="btn" onClick={async () => {
                if (!proposalId) return;
                setSimResult(await simulateCommercialProposal(proposalId, { fraccion_valor: 0.3 }));
              }}>Simular sin guardar</button>
            )}
            {has("comercial.view") && (
              <button type="button" className="btn" onClick={async () => {
                if (!proposalId) return;
                await detectCommercialDoubleCount(proposalId);
                await reload();
              }}>Detectar doble conteo</button>
            )}
          </div>
          {simResult && (
            <div className="metrics-grid compact-metrics">
              <div><strong>Simulado</strong><span>{formatMoney(simResult.precio_sugerido as number, currency)}</span></div>
              <div><strong>ROI sim.</strong><span>{formatPct(simResult.roi_pct as number | null)}</span></div>
            </div>
          )}
          {has("comercial.approve") && (
            <form className="form-grid compact-form" onSubmit={async (e: FormEvent) => {
              e.preventDefault();
              if (!proposalId || !precioFinal) return;
              await setCommercialFinalPrice(proposalId, { precio_final: Number(precioFinal), justificacion });
              await reload();
            }}>
              <label>Precio final<input value={precioFinal} onChange={(e) => setPrecioFinal(e.target.value)} /></label>
              <label>Justificación<input value={justificacion} onChange={(e) => setJustificacion(e.target.value)} /></label>
              <button type="submit" className="btn primary">Establecer precio final</button>
              <button type="button" className="btn" onClick={async () => {
                if (!proposalId) return;
                await approveCommercialProposal(proposalId);
                await reload();
              }}>Aprobar propuesta</button>
            </form>
          )}
          <h3>Escenarios</h3>
          <table className="data-table compact-table">
            <thead><tr><th>Tipo</th><th>Esperado</th><th>Atribuible</th><th>Prob.</th></tr></thead>
            <tbody>
              {detail.escenarios.map((s) => (
                <tr key={s.scenario_type}>
                  <td>{s.scenario_type}</td>
                  <td>{formatMoney(s.valor_esperado, currency)}</td>
                  <td>{formatMoney(s.valor_atribuible, currency)}</td>
                  <td>{s.probabilidad ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {tab === "trazabilidad" && (
        <section className="panel compact-panel">
          <h2>Seguimiento del valor</h2>
          <div className="metrics-grid compact-metrics">
            <div><strong>Oportunidades</strong><span>{((trace?.oportunidades as string[]) ?? []).length}</span></div>
            <div><strong>Valoraciones 1210</strong><span>{((trace?.valoraciones_1210 as string[]) ?? []).length}</span></div>
            <div><strong>Líneas base 1200</strong><span>{((trace?.lineas_base_1200 as string[]) ?? []).length}</span></div>
            <div><strong>Referencias FinOps</strong><span>{((trace?.finops_refs as string[]) ?? []).length}</span></div>
          </div>
          {detail.alertas_doble_conteo.length > 0 && (
            <div className="alert-box">
              <h3>Alertas doble conteo</h3>
              {detail.alertas_doble_conteo.map((a) => (
                <p key={a.id}><strong>{a.severidad}</strong>: {a.mensaje}</p>
              ))}
            </div>
          )}
          {trace?.contrato_centro_control && (
            <details className="compact-details">
              <summary>Contrato preparado para Centro de Control (sin cablear)</summary>
              <pre className="compact-pre">{JSON.stringify(trace.contrato_centro_control, null, 2)}</pre>
            </details>
          )}
          <p className="muted">
            <Link to="/tco">Ver TCO →</Link> · <Link to="/implementacion">Ver implementación →</Link>
          </p>
        </section>
      )}
    </div>
  );
}
