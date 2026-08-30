import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  createCommercialProposal,
  fetchCommercialPlans,
  fetchCommercialProposals,
  simulateCommercialValue,
  type CommercialPlanItem,
  type CommercialProposalSummary,
} from "../api";
import { HelpTooltip } from "../components/comercial/HelpTooltip";
import { formatMoney, TOOLTIPS } from "../lib/comercialLabels";
import { usePermissions } from "../hooks/usePermissions";

type Tab = "propuestas" | "planes" | "simulador";

export function ComercialPage() {
  const { has } = usePermissions();
  const [tab, setTab] = useState<Tab>("propuestas");
  const [plans, setPlans] = useState<CommercialPlanItem[]>([]);
  const [proposals, setProposals] = useState<CommercialProposalSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");
  const [sim, setSim] = useState<Record<string, unknown> | null>(null);
  const [simForm, setSimForm] = useState({ valor_bruto: "100000", atribucion_pct: "40", costo_total: "15000" });

  useEffect(() => {
    Promise.all([fetchCommercialPlans(), fetchCommercialProposals()])
      .then(([p, pr]) => { setPlans(p); setProposals(pr); })
      .catch((e) => setError(e instanceof Error ? e.message : "Error"))
      .finally(() => setLoading(false));
  }, []);

  const filteredProposals = proposals.filter(
    (p) => !filter || p.codigo.toLowerCase().includes(filter.toLowerCase()) || p.titulo.toLowerCase().includes(filter.toLowerCase()),
  );

  async function onSimulate(e: FormEvent) {
    e.preventDefault();
    setSim(await simulateCommercialValue({
      valor_bruto: Number(simForm.valor_bruto),
      atribucion_pct: Number(simForm.atribucion_pct),
      costo_total: Number(simForm.costo_total),
    }));
  }

  async function onCreateProposal() {
    const created = await createCommercialProposal({ titulo: `Propuesta ${new Date().toLocaleDateString("es-CO")}` });
    window.location.href = `/comercial/propuestas/${created.id}`;
  }

  return (
    <div className="ops-page">
      <header className="ops-header">
        <h1>Comercial y valor</h1>
        <p className="muted">Propuestas, planes, valor económico y precio basado en valor generado.</p>
        <div className="ops-actions">
          <Link to="/comercial/segmentacion" className="btn">Segmentación y planes →</Link>
          <Link to="/costos-valor" className="btn">Costos IA (FinOps) →</Link>
          <Link to="/tco" className="btn">TCO →</Link>
        </div>
      </header>
      {error && <p className="error-text">{error}</p>}

      <nav className="tab-nav compact-tabs">
        {(["propuestas", "planes", "simulador"] as Tab[]).map((t) => (
          <button key={t} type="button" className={tab === t ? "active" : ""} onClick={() => setTab(t)}>
            {t === "propuestas" ? "Propuestas" : t === "planes" ? "Planes" : "Simulador"}
          </button>
        ))}
      </nav>

      {loading ? <p>Cargando…</p> : (
        <>
          {tab === "propuestas" && (
            <section className="panel compact-panel">
              <div className="panel-header-row">
                <h2>Propuestas comerciales</h2>
                {has("comercial.create") && <button type="button" className="btn primary" onClick={onCreateProposal}>Nueva propuesta</button>}
              </div>
              <input className="ops-input filter-input" placeholder="Buscar por código o título…" value={filter} onChange={(e) => setFilter(e.target.value)} />
              <table className="data-table compact-table">
                <thead>
                  <tr><th>Código</th><th>Título</th><th>Estado</th><th>Valor atribuible</th><th>Precio</th></tr>
                </thead>
                <tbody>
                  {filteredProposals.map((p) => (
                    <tr key={p.id}>
                      <td><Link to={`/comercial/propuestas/${p.id}`}>{p.codigo}</Link></td>
                      <td>{p.titulo}</td>
                      <td>{p.estado}</td>
                      <td>{formatMoney(p.valor_atribuible_total)}</td>
                      <td>{formatMoney(p.precio_final ?? p.precio_sugerido)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}

          {tab === "planes" && (
            <section className="panel compact-panel">
              <div className="notice-banner subtle">Sin IA ilimitada: cada plan define cupos de consumo IA.</div>
              <table className="data-table compact-table">
                <thead>
                  <tr><th>Plan</th><th>Modalidad IA</th><th>Tokens incl.</th><th>Presupuesto IA</th><th></th></tr>
                </thead>
                <tbody>
                  {plans.map((pl) => (
                    <tr key={pl.id}>
                      <td>{pl.name} <span className="muted">({pl.code})</span></td>
                      <td>{pl.credential_mode === "CREDENCIALES_PROPIAS" ? "Credenciales propias" : "IA administrada"}</td>
                      <td>{pl.consumo_ia_incluido_tokens?.toLocaleString("es-CO") ?? "—"}</td>
                      <td>{formatMoney(pl.presupuesto_ia_incluido)}</td>
                      <td><Link to={`/comercial/planes/${pl.id}`}>Ver detalle</Link></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}

          {tab === "simulador" && (
            <section className="panel compact-panel">
              <h2>Simulador rápido de valor</h2>
              <form onSubmit={onSimulate} className="form-grid compact-form">
                <label>Valor bruto<input value={simForm.valor_bruto} onChange={(e) => setSimForm({ ...simForm, valor_bruto: e.target.value })} /></label>
                <label>% atribuible<input value={simForm.atribucion_pct} onChange={(e) => setSimForm({ ...simForm, atribucion_pct: e.target.value })} /></label>
                <label>Costo total<input value={simForm.costo_total} onChange={(e) => setSimForm({ ...simForm, costo_total: e.target.value })} /></label>
                {has("comercial.simulate") && <button type="submit" className="btn primary">Simular</button>}
              </form>
              {sim && (
                <div className="metrics-grid compact-metrics">
                  <div><strong>Valor atribuible</strong><span>{formatMoney(sim.valor_atribuible as number)}</span></div>
                  <div><strong>Precio sugerido</strong><span>{formatMoney(sim.precio_sugerido as number)}</span></div>
                  <div><strong>Beneficio neto</strong><span>{formatMoney(sim.beneficio_neto_cliente as number)}</span></div>
                  <div><strong>ROI</strong><span>{String(sim.roi_pct ?? "—")}% <HelpTooltip text={TOOLTIPS.roi} /></span></div>
                  <div><strong>Payback</strong><span>{String(sim.payback_meses ?? "—")} meses <HelpTooltip text={TOOLTIPS.payback} /></span></div>
                </div>
              )}
            </section>
          )}
        </>
      )}
    </div>
  );
}
