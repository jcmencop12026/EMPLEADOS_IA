import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import type { OptimizacionRecomendacion } from "../api";
import {
  aprobarRecomendacionOptimizacion,
  confirmarEjecucionHumanaOptimizacion,
  ejecutarRecomendacionOptimizacion,
  fetchOptimizacionRecomendacion,
} from "../api";
import { ExecutionStatusPanel } from "../components/optimizacion/ExecutionStatusPanel";
import { HelpTooltip } from "../components/optimizacion/HelpTooltip";
import { EstadoBadge } from "../components/optimizacion/EstadoBadge";
import { SemanticBadge } from "../components/optimizacion/SemanticBadge";
import { TOOLTIPS } from "../lib/optimizacionLabels";

export function OptimizacionDetailPage() {
  const { recId } = useParams<{ recId: string }>();
  const [detail, setDetail] = useState<OptimizacionRecomendacion | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function load() {
    if (!recId) return;
    fetchOptimizacionRecomendacion(recId)
      .then(setDetail)
      .catch((e) => setError(e instanceof Error ? e.message : "Error"));
  }

  useEffect(() => {
    load();
  }, [recId]);

  async function onAprobar() {
    if (!recId) return;
    const justificacion = window.prompt("Justificación de aprobación:");
    if (!justificacion) return;
    setBusy(true);
    try {
      await aprobarRecomendacionOptimizacion(recId, justificacion);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al aprobar");
    } finally {
      setBusy(false);
    }
  }

  async function onEjecutar(tipo: "AUTOMATICA" | "HUMANA_EXTERNA") {
    if (!recId) return;
    setBusy(true);
    setError(null);
    try {
      await ejecutarRecomendacionOptimizacion(recId, tipo);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al ejecutar");
    } finally {
      setBusy(false);
    }
  }

  async function onConfirmarHumana() {
    if (!recId) return;
    const ref = window.prompt("Referencia externa de ejecución:");
    if (!ref) return;
    setBusy(true);
    try {
      await confirmarEjecucionHumanaOptimizacion(recId, ref);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al confirmar ejecución");
    } finally {
      setBusy(false);
    }
  }

  if (!detail) {
    return <div className="page"><p className="muted">Cargando…</p></div>;
  }

  const ejecEstado = detail.ejecucion?.estado;
  const puedeEjecutar = detail.estado === "APROBADA" && detail.factible && !ejecEstado;
  const pendienteHumana = ejecEstado === "PENDIENTE_EJECUCION_HUMANA";
  const seleccionados = (detail.items ?? []).filter((i) => i.seleccionado);
  const excluidos = (detail.items ?? []).filter((i) => !i.seleccionado);

  return (
    <div className="page">
      <header className="page-header compact">
        <p className="muted"><Link to="/optimizacion">← Optimización</Link></p>
        <h1>{detail.codigo} <SemanticBadge kind="RECOMENDACION" /></h1>
        <p className="muted">
          {detail.objetivo} — <EstadoBadge estado={detail.estado} />
          {ejecEstado && <> / <EstadoBadge estado={ejecEstado} tipo="ejecucion" /></>}
        </p>
      </header>

      {error && <div className="alert alert-error">{error}</div>}

      {!detail.factible && (
        <div className="alert alert-error">
          Sin solución factible: {(detail.conflictos as string[])?.join("; ") ?? "Restricciones en conflicto"}
        </div>
      )}

      <section className="card compact-panel" style={{ marginBottom: "1rem" }}>
        <h2>Resumen</h2>
        <div className="compact-metrics">
          <div><span className="muted">Valor esperado</span><strong>{detail.valor_esperado_total?.toLocaleString("es-CO")}</strong></div>
          <div><span className="muted">Costo</span><strong>{detail.costo_esperado_total?.toLocaleString("es-CO")}</strong></div>
          <div><span className="muted">ROI</span><strong>{detail.roi_esperado != null ? detail.roi_esperado.toFixed(2) : "—"}</strong></div>
          <div><span className="muted">Riesgo prom.</span><strong>{detail.riesgo_promedio != null ? detail.riesgo_promedio.toFixed(2) : "—"}</strong></div>
          <div><span className="muted">Confianza</span><strong>{detail.confianza_promedio != null ? detail.confianza_promedio.toFixed(2) : "—"}</strong></div>
        </div>
        <div style={{ marginTop: 8, display: "flex", gap: 8, flexWrap: "wrap" }}>
          {detail.estado === "PROPUESTA" && (
            <button type="button" className="btn btn-primary btn-sm" onClick={onAprobar} disabled={busy}>
              Aprobar recomendación
            </button>
          )}
          {puedeEjecutar && (
            <>
              <button type="button" className="btn btn-primary btn-sm" onClick={() => onEjecutar("AUTOMATICA")} disabled={busy}>
                Ejecutar automáticamente
              </button>
              <button type="button" className="btn btn-sm" onClick={() => onEjecutar("HUMANA_EXTERNA")} disabled={busy}>
                Marcar pendiente humana
              </button>
            </>
          )}
          {pendienteHumana && (
            <button type="button" className="btn btn-secondary btn-sm" onClick={onConfirmarHumana} disabled={busy}>
              Confirmar ejecución humana
            </button>
          )}
        </div>
      </section>

      <ExecutionStatusPanel detail={detail} />

      <section className="card compact-panel" style={{ marginBottom: "1rem" }}>
        <h2>Selección recomendada</h2>
        <table className="data-table compact-table">
          <thead>
            <tr><th>Orden</th><th>Oportunidad</th><th>Puntuación</th><th>Riesgo</th><th>Confianza</th><th>Aprendizaje</th></tr>
          </thead>
          <tbody>
            {seleccionados.map((i) => (
              <tr key={i.opportunity_id}>
                <td>{i.orden}</td>
                <td><Link to={`/oportunidades/${i.opportunity_id}`}>{i.opportunity_id.slice(0, 8)}…</Link></td>
                <td>{i.puntuacion_total}</td>
                <td>{i.riesgo ?? "—"}</td>
                <td>{i.confianza ?? "—"}</td>
                <td>{i.aprendizaje ? <SemanticBadge kind="INFERENCIA" /> : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {excluidos.length > 0 && (
        <section className="card compact-panel" style={{ marginBottom: "1rem" }}>
          <h2>Excluidas</h2>
          <ul>
            {excluidos.map((i) => (
              <li key={i.opportunity_id}>{i.opportunity_id.slice(0, 8)}… — {i.exclusion_razon}</li>
            ))}
          </ul>
        </section>
      )}

      {detail.aprendizaje_influencia && (
        <section className="card compact-panel" style={{ marginBottom: "1rem" }}>
          <h2>Influencia de aprendizaje <HelpTooltip text={TOOLTIPS.aprendizaje} /></h2>
          <pre className="compact-pre">{JSON.stringify(detail.aprendizaje_influencia, null, 2)}</pre>
        </section>
      )}

      {detail.explicacion && (
        <section className="card compact-panel">
          <h2>Explicación</h2>
          <pre className="compact-pre">{JSON.stringify(detail.explicacion, null, 2)}</pre>
        </section>
      )}
    </div>
  );
}
