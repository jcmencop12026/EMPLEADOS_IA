import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import type { RecalibracionItem, RetroalimentacionItem } from "../api";
import {
  aplicarRecalibracion,
  aprobarRecalibracion,
  evaluarCicloAprendizaje,
  fetchCicloAprendizaje,
  fetchHistorialAprendizaje,
  rechazarRecalibracion,
} from "../api";
import { HelpTooltip } from "../components/optimizacion/HelpTooltip";
import { EstadoBadge } from "../components/optimizacion/EstadoBadge";
import { SemanticBadge } from "../components/optimizacion/SemanticBadge";
import {
  extractCorrelationId,
  sinCambioPrioridad,
  TIPO_EXPLICACION_SEMANTICA,
  TOOLTIPS,
} from "../lib/optimizacionLabels";

export function AprendizajeDetailPage() {
  const { cicloId } = useParams<{ cicloId: string }>();
  const [detail, setDetail] = useState<Awaited<ReturnType<typeof fetchCicloAprendizaje>> | null>(null);
  const [historial, setHistorial] = useState<unknown[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [valorReal, setValorReal] = useState("");
  const [impactoReal, setImpactoReal] = useState("");

  function load() {
    if (!cicloId) return;
    Promise.all([fetchCicloAprendizaje(cicloId), fetchHistorialAprendizaje(cicloId)])
      .then(([d, h]) => {
        setDetail(d);
        setHistorial(h);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar ciclo"));
  }

  useEffect(() => {
    load();
  }, [cicloId]);

  async function onEvaluar() {
    if (!cicloId) return;
    setBusy(true);
    setError(null);
    try {
      await evaluarCicloAprendizaje(cicloId, {
        valor_real: valorReal ? Number(valorReal) : undefined,
        impacto_real: impactoReal ? Number(impactoReal) : undefined,
        tipo_explicacion: "PROBABLE",
      });
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo evaluar");
    } finally {
      setBusy(false);
    }
  }

  async function onAprobar(rec: RecalibracionItem) {
    setBusy(true);
    try {
      await aprobarRecalibracion(rec.id);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al aprobar");
    } finally {
      setBusy(false);
    }
  }

  async function onRechazar(rec: RecalibracionItem) {
    const motivo = window.prompt("Motivo del rechazo:");
    if (!motivo) return;
    setBusy(true);
    try {
      await rechazarRecalibracion(rec.id, motivo);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al rechazar");
    } finally {
      setBusy(false);
    }
  }

  async function onAplicar(rec: RecalibracionItem) {
    setBusy(true);
    try {
      await aplicarRecalibracion(rec.id);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al aplicar");
    } finally {
      setBusy(false);
    }
  }

  if (!detail) {
    return <div className="page"><p className="muted">Cargando ciclo…</p></div>;
  }

  const desviaciones = (detail.desviaciones ?? {}) as Record<string, { esperado?: number; real?: number; direccion?: string }>;
  const correlationId = extractCorrelationId(detail.referencias);
  const sinCambio = sinCambioPrioridad(detail.prioridad_anterior, detail.prioridad_propuesta);
  const retro = (detail.retroalimentaciones ?? []) as RetroalimentacionItem[];

  return (
    <div className="page">
      <header className="page-header compact">
        <p className="muted"><Link to="/aprendizaje">← Aprendizaje</Link></p>
        <h1>Ciclo {detail.id.slice(0, 8)}…</h1>
        <p className="muted">
          Oportunidad <Link to={`/oportunidades/${detail.opportunity_id}`}>{detail.opportunity_id.slice(0, 8)}…</Link>
          {" — "}<EstadoBadge estado={detail.estado} />
        </p>
      </header>

      {error && <div className="alert alert-error">{error}</div>}

      <section className="card compact-panel" style={{ marginBottom: "1rem" }}>
        <h2>Origen y trazabilidad</h2>
        <div className="compact-metrics">
          <div><span className="muted">Organización</span><strong className="mono">{detail.organization_id?.slice(0, 8) ?? "—"}</strong></div>
          <div><span className="muted">Plan de trabajo</span><strong className="mono">{detail.work_plan_id?.slice(0, 8) ?? "—"}</strong></div>
          <div><span className="muted">Señal origen</span><strong className="mono">{detail.signal_id?.slice(0, 8) ?? "—"}</strong></div>
          <div>
            <span className="muted">ID de correlación<HelpTooltip text={TOOLTIPS.correlation_id} /></span>
            <strong className="mono">{correlationId ?? "—"}</strong>
          </div>
          <div><span className="muted">Evaluado</span><strong>{detail.evaluado_at ? new Date(detail.evaluado_at).toLocaleString("es-CO") : "—"}</strong></div>
        </div>
      </section>

      <section className="card compact-panel" style={{ marginBottom: "1rem" }}>
        <h2>Resultado esperado vs observado</h2>
        <table className="data-table compact-table">
          <thead><tr><th>Métrica</th><th>Esperado</th><th>Observado</th><th>Diferencia</th></tr></thead>
          <tbody>
            {[
              ["Impacto", detail.impacto_esperado, detail.impacto_real, desviaciones.impacto],
              ["Valor", detail.valor_esperado, detail.valor_real, desviaciones.valor],
              ["Costo", detail.costo_esperado, detail.costo_real, desviaciones.costo],
              ["Tiempo (días)", detail.tiempo_esperado_dias, detail.tiempo_real_dias, desviaciones.tiempo],
            ].map(([label, esp, real, dev]) => (
              <tr key={String(label)}>
                <td>{label}</td>
                <td>{esp ?? "—"}</td>
                <td>{real ?? "—"}</td>
                <td>{dev?.direccion ?? (esp != null && real != null ? Number(real) - Number(esp) : "—")}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {detail.estado === "ABIERTO" && (
          <div style={{ marginTop: 8, display: "flex", gap: 8, flexWrap: "wrap" }}>
            <input type="number" placeholder="Valor observado" value={valorReal} onChange={(e) => setValorReal(e.target.value)} />
            <input type="number" placeholder="Impacto observado" value={impactoReal} onChange={(e) => setImpactoReal(e.target.value)} />
            <button type="button" className="btn btn-primary btn-sm" onClick={onEvaluar} disabled={busy}>Evaluar ciclo</button>
          </div>
        )}
      </section>

      <section className="card compact-panel" style={{ marginBottom: "1rem" }}>
        <h2>Aprendizaje generado</h2>
        {retro.length === 0 ? (
          <p className="muted">Sin retroalimentación registrada aún.</p>
        ) : (
          retro.map((r) => {
            const sem = TIPO_EXPLICACION_SEMANTICA[r.tipo_explicacion] ?? "INFERENCIA";
            return (
              <div key={r.id} className="approval-card">
                <div className="panel-header-row">
                  <strong>{r.resumen ?? "Aprendizaje"}</strong>
                  <SemanticBadge kind={sem} />
                </div>
                <p>{r.detalle ?? "—"}</p>
                <p className="muted">Calidad recomendación: {r.calidad_recomendacion ?? "—"}</p>
                {(r.lecciones?.length ?? 0) > 0 && (
                  <ul>
                    {(r.lecciones as string[]).map((l, i) => <li key={i}>{l}</li>)}
                  </ul>
                )}
                <p className="muted">{r.created_at ? new Date(r.created_at).toLocaleString("es-CO") : ""}</p>
              </div>
            );
          })
        )}
      </section>

      <section className="card compact-panel" style={{ marginBottom: "1rem" }}>
        <h2>Repriorización <HelpTooltip text={TOOLTIPS.repriorizacion} /></h2>
        {sinCambio ? (
          <p className="notice-banner subtle">No hubo cambio de prioridad en este ciclo.</p>
        ) : (
          <p>Prioridad {detail.prioridad_anterior ?? "—"} → <strong>{detail.prioridad_propuesta ?? "—"}</strong></p>
        )}
        {detail.explicacion_prioridad && (
          <pre className="compact-pre">{JSON.stringify(detail.explicacion_prioridad, null, 2)}</pre>
        )}
        {(detail.recalibraciones ?? []).length > 0 && (
          <table className="data-table compact-table" style={{ marginTop: 8 }}>
            <thead><tr><th>Campo</th><th>Estado</th><th>Anterior</th><th>Nuevo</th><th>Evidencia</th><th></th></tr></thead>
            <tbody>
              {(detail.recalibraciones ?? []).map((rec) => (
                <tr key={rec.id}>
                  <td>{rec.campo}</td>
                  <td>{rec.estado}</td>
                  <td>{rec.valor_anterior ?? "—"}</td>
                  <td>{rec.valor_nuevo ?? "—"}</td>
                  <td>{rec.justificacion}</td>
                  <td>
                    {rec.estado === "SUGERIDA" && (
                      <>
                        <button type="button" className="btn btn-sm" onClick={() => onAprobar(rec)} disabled={busy}>Aprobar</button>{" "}
                        <button type="button" className="btn btn-sm" onClick={() => onRechazar(rec)} disabled={busy}>Rechazar</button>
                      </>
                    )}
                    {rec.estado === "APROBADA" && (
                      <button type="button" className="btn btn-sm btn-primary" onClick={() => onAplicar(rec)} disabled={busy}>Aplicar</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="card compact-panel">
        <h2>Historial auditable</h2>
        {historial.length === 0 ? (
          <p className="muted">Sin eventos.</p>
        ) : (
          <ul>
            {(historial as { accion: string; created_at?: string }[]).map((h, i) => (
              <li key={i}>{h.created_at ? new Date(h.created_at).toLocaleString("es-CO") : ""} — {h.accion}</li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
