import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  createCommercialPlan,
  createCommercialProposal,
  fetchCommercialPlans,
  fetchCommercialProposals,
  simulateCommercialValue,
  type CommercialPlanItem,
  type CommercialProposalSummary,
} from "../api";
import { usePermissions } from "../hooks/usePermissions";

export function ComercialPage() {
  const { has } = usePermissions();
  const [plans, setPlans] = useState<CommercialPlanItem[]>([]);
  const [proposals, setProposals] = useState<CommercialProposalSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sim, setSim] = useState<Record<string, unknown> | null>(null);
  const [simForm, setSimForm] = useState({ valor_bruto: "100000", atribucion_pct: "40", costo_total: "15000" });

  useEffect(() => {
    Promise.all([fetchCommercialPlans(), fetchCommercialProposals()])
      .then(([p, pr]) => {
        setPlans(p);
        setProposals(pr);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Error"))
      .finally(() => setLoading(false));
  }, []);

  async function onSimulate(e: FormEvent) {
    e.preventDefault();
    const result = await simulateCommercialValue({
      valor_bruto: Number(simForm.valor_bruto),
      atribucion_pct: Number(simForm.atribucion_pct),
      costo_total: Number(simForm.costo_total),
    });
    setSim(result);
  }

  async function onCreateProposal() {
    const created = await createCommercialProposal({ titulo: `Propuesta ${new Date().toLocaleDateString("es-CO")}` });
    window.location.href = `/comercial/propuestas/${created.id}`;
  }

  return (
    <div className="ops-page">
      <header className="ops-header">
        <h1>Modelo comercial basado en valor</h1>
        <p>Planes, simulación y propuestas trazables al valor económico.</p>
        <Link to="/comercial/segmentacion">Segmentación y planes verticales →</Link>
      </header>
      {error && <p className="error-text">{error}</p>}
      {loading ? (
        <p>Cargando…</p>
      ) : (
        <>
          <section className="panel">
            <h2>Simulador de valor</h2>
            <form onSubmit={onSimulate} className="form-grid">
              <label>
                Valor bruto
                <input value={simForm.valor_bruto} onChange={(e) => setSimForm({ ...simForm, valor_bruto: e.target.value })} />
              </label>
              <label>
                % atribuible EMPLEADOS_IA
                <input value={simForm.atribucion_pct} onChange={(e) => setSimForm({ ...simForm, atribucion_pct: e.target.value })} />
              </label>
              <label>
                Costo total
                <input value={simForm.costo_total} onChange={(e) => setSimForm({ ...simForm, costo_total: e.target.value })} />
              </label>
              {has("comercial.simulate") && <button type="submit">Simular</button>}
            </form>
            {sim && (
              <div className="metrics-grid">
                <div><strong>Valor atribuible</strong><span>{String(sim.valor_atribuible)}</span></div>
                <div><strong>Precio sugerido</strong><span>{String(sim.precio_sugerido)}</span></div>
                <div><strong>Beneficio neto cliente</strong><span>{String(sim.beneficio_neto_cliente)}</span></div>
                <div><strong>ROI %</strong><span>{String(sim.roi_pct ?? "—")}</span></div>
                <div><strong>Payback (meses)</strong><span>{String(sim.payback_meses ?? "—")}</span></div>
              </div>
            )}
          </section>

          <section className="panel">
            <div className="panel-header-row">
              <h2>Propuestas comerciales</h2>
              {has("comercial.create") && <button onClick={onCreateProposal}>Nueva propuesta</button>}
            </div>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Código</th>
                  <th>Título</th>
                  <th>Estado</th>
                  <th>Valor atribuible</th>
                  <th>Precio sugerido</th>
                </tr>
              </thead>
              <tbody>
                {proposals.map((p) => (
                  <tr key={p.id}>
                    <td><Link to={`/comercial/propuestas/${p.id}`}>{p.codigo}</Link></td>
                    <td>{p.titulo}</td>
                    <td>{p.estado}</td>
                    <td>{p.valor_atribuible_total ?? "—"}</td>
                    <td>{p.precio_sugerido ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="panel">
            <h2>Planes comerciales</h2>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Código</th>
                  <th>Nombre</th>
                  <th>Consumo IA incluido</th>
                  <th>Margen mínimo</th>
                </tr>
              </thead>
              <tbody>
                {plans.map((pl) => (
                  <tr key={pl.id}>
                    <td>{pl.code}</td>
                    <td>{pl.name}</td>
                    <td>{pl.consumo_ia_incluido_tokens ?? pl.presupuesto_ia_incluido ?? "—"}</td>
                    <td>{(pl.margen_minimo_pct * 100).toFixed(0)}%</td>
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
