import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  addCommercialCost,
  addCommercialScenario,
  addCommercialValue,
  approveCommercialProposal,
  detectCommercialDoubleCount,
  fetchCommercialProposal,
  setCommercialFinalPrice,
  suggestCommercialPrice,
  type CommercialProposalDetail,
} from "../api";
import { usePermissions } from "../hooks/usePermissions";

export function ComercialPropuestaDetailPage() {
  const { proposalId } = useParams<{ proposalId: string }>();
  const { has } = usePermissions();
  const [detail, setDetail] = useState<CommercialProposalDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [precioFinal, setPrecioFinal] = useState("");
  const [justificacion, setJustificacion] = useState("");

  function reload() {
    if (!proposalId) return;
    fetchCommercialProposal(proposalId).then(setDetail).catch((e) => setError(e.message));
  }

  useEffect(() => {
    reload();
  }, [proposalId]);

  async function onSuggest() {
    if (!proposalId) return;
    await suggestCommercialPrice(proposalId);
    reload();
  }

  async function onAddValue(e: FormEvent) {
    e.preventDefault();
    if (!proposalId) return;
    await addCommercialValue(proposalId, {
      categoria: "AHORRO",
      naturaleza: "ESTIMADO",
      valor_bruto: 100000,
      atribucion_pct: 35,
      criterio_atribucion: "Impacto directo atribuible a automatización",
    });
    reload();
  }

  async function onAddScenario() {
    if (!proposalId) return;
    for (const [tipo, mult] of [
      ["CONSERVADOR", 0.7],
      ["BASE", 1],
      ["ALTO", 1.3],
    ] as const) {
      await addCommercialScenario(proposalId, {
        scenario_type: tipo,
        valor_esperado: 100000 * mult,
        valor_atribuible: 35000 * mult,
        probabilidad: tipo === "CONSERVADOR" ? 0.6 : tipo === "BASE" ? 0.75 : 0.5,
        costo: 15000,
        es_recomendado: tipo === "BASE",
        explicacion: `Escenario ${tipo.toLowerCase()}`,
      });
    }
    reload();
  }

  async function onAddCost() {
    if (!proposalId) return;
    await addCommercialCost(proposalId, { categoria: "CONSUMO_IA", clase_costo: "COSTO_PROVEEDOR_IA", monto: 5000 });
    await addCommercialCost(proposalId, { categoria: "IMPLEMENTACION", clase_costo: "COSTO_INTERNO", monto: 10000 });
    reload();
  }

  async function onDetectDouble() {
    if (!proposalId) return;
    await detectCommercialDoubleCount(proposalId);
    reload();
  }

  async function onSetFinal(e: FormEvent) {
    e.preventDefault();
    if (!proposalId || !precioFinal) return;
    await setCommercialFinalPrice(proposalId, { precio_final: Number(precioFinal), justificacion });
    reload();
  }

  async function onApprove() {
    if (!proposalId) return;
    await approveCommercialProposal(proposalId);
    reload();
  }

  if (!detail) return <p>Cargando propuesta…</p>;

  return (
    <div className="ops-page">
      <header className="ops-header">
        <Link to="/comercial">← Comercial</Link>
        <h1>{detail.codigo} — {detail.titulo}</h1>
        <p>Estado: {detail.estado} · Escenario recomendado: {detail.escenario_recomendado}</p>
      </header>
      {error && <p className="error-text">{error}</p>}

      <section className="metrics-grid">
        <div><strong>Valor atribuible</strong><span>{detail.valor_atribuible_total ?? "—"}</span></div>
        <div><strong>Costo EMPLEADOS_IA</strong><span>{detail.costo_total ?? "—"}</span></div>
        <div><strong>Precio sugerido</strong><span>{detail.precio_sugerido ?? "—"}</span></div>
        <div><strong>Precio final</strong><span>{detail.precio_final ?? "—"}</span></div>
        <div><strong>Beneficio neto cliente</strong><span>{detail.beneficio_neto_cliente ?? "—"}</span></div>
        <div><strong>ROI %</strong><span>{detail.roi_pct ?? "—"}</span></div>
        <div><strong>Payback (meses)</strong><span>{detail.payback_meses ?? "—"}</span></div>
        <div><strong>Margen %</strong><span>{detail.margen_pct ?? "—"}</span></div>
        <div><strong>% valor conservado cliente</strong><span>{detail.pct_valor_conservado_cliente ?? "—"}</span></div>
      </section>

      <section className="panel">
        <h2>Escenarios</h2>
        <table className="data-table">
          <thead><tr><th>Tipo</th><th>Valor esperado</th><th>Valor atribuible</th><th>Prob.</th><th>Recomendado</th></tr></thead>
          <tbody>
            {detail.escenarios.map((s) => (
              <tr key={s.scenario_type}>
                <td>{s.scenario_type}</td>
                <td>{s.valor_esperado ?? "—"}</td>
                <td>{s.valor_atribuible ?? "—"}</td>
                <td>{s.probabilidad ?? "—"}</td>
                <td>{s.es_recomendado ? "Sí" : "No"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {has("comercial.create") && <button onClick={onAddScenario}>Agregar escenarios ejemplo</button>}
      </section>

      <section className="panel">
        <h2>Componentes de valor</h2>
        <ul>
          {detail.valores.map((v) => (
            <li key={v.id}>{v.categoria} ({v.naturaleza}): bruto {v.valor_bruto} → atribuible {v.valor_atribuible} ({v.atribucion_pct}%)</li>
          ))}
        </ul>
        {has("comercial.create") && <button onClick={onAddValue}>Agregar valor ejemplo</button>}
      </section>

      <section className="panel">
        <h2>Costos</h2>
        <ul>
          {detail.costos.map((c) => (
            <li key={c.id}>{c.categoria} ({c.clase_costo}): {c.monto}</li>
          ))}
        </ul>
        {has("comercial.create") && <button onClick={onAddCost}>Agregar costos ejemplo</button>}
      </section>

      {detail.alertas_doble_conteo.length > 0 && (
        <section className="panel">
          <h2>Alertas doble conteo</h2>
          <ul>{detail.alertas_doble_conteo.map((a) => <li key={a.id}><strong>{a.severidad}</strong>: {a.mensaje}</li>)}</ul>
        </section>
      )}

      <section className="panel actions-row">
        {has("comercial.simulate") && <button onClick={onSuggest}>Calcular precio sugerido</button>}
        {has("comercial.view") && <button onClick={onDetectDouble}>Detectar doble conteo</button>}
      </section>

      {has("comercial.approve") && (
        <section className="panel">
          <h2>Aprobación humana de precio</h2>
          <form onSubmit={onSetFinal} className="form-grid">
            <label>Precio final<input value={precioFinal} onChange={(e) => setPrecioFinal(e.target.value)} /></label>
            <label>Justificación<input value={justificacion} onChange={(e) => setJustificacion(e.target.value)} /></label>
            <button type="submit">Establecer precio final</button>
            <button type="button" onClick={onApprove}>Aprobar propuesta</button>
          </form>
        </section>
      )}

      <section className="panel">
        <h2>Trazabilidad</h2>
        <pre>{JSON.stringify(detail.trazabilidad, null, 2)}</pre>
      </section>
    </div>
  );
}
