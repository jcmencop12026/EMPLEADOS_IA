import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import type { LineaBaseDetail } from "../api";
import {
  addLineaBaseMedicion,
  fetchLineaBase,
  updateLineaBaseAtribucion,
  validateLineaBaseMedicion,
} from "../api";
import { usePermissions } from "../hooks/usePermissions";

const EVAL_LABELS: Record<string, string> = {
  MEJORA: "Mejora",
  DETERIORO: "Deterioro",
  SIN_CAMBIO: "Sin cambio",
  INFORMATIVO: "Informativo",
};

const TIPO_IMPACTO_LABELS: Record<string, string> = {
  IMPACTO_ESPERADO: "Impacto esperado",
  IMPACTO_REAL: "Impacto real medido",
  CAMBIO_OBSERVADO: "Cambio observado",
  VALOR_ATRIBUIDO: "Valor atribuido",
};

export function LineaBaseDetailPage() {
  const { lineaBaseId } = useParams<{ lineaBaseId: string }>();
  const { has } = usePermissions();
  const [data, setData] = useState<LineaBaseDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [valorPosterior, setValorPosterior] = useState("");
  const [periodoInicio, setPeriodoInicio] = useState("");
  const [periodoFin, setPeriodoFin] = useState("");
  const [evidencia, setEvidencia] = useState("");

  async function reload() {
    if (!lineaBaseId) return;
    setLoading(true);
    try {
      const res = await fetchLineaBase(lineaBaseId);
      setData(res);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void reload();
  }, [lineaBaseId]);

  async function onAddMedicion(e: FormEvent) {
    e.preventDefault();
    if (!lineaBaseId || !valorPosterior) return;
    try {
      await addLineaBaseMedicion(lineaBaseId, {
        valor_posterior: Number(valorPosterior),
        periodo_inicio: new Date(periodoInicio).toISOString(),
        periodo_fin: new Date(periodoFin).toISOString(),
        fuente: "MANUAL",
        evidencia: evidencia.trim() ? { nota: evidencia.trim() } : undefined,
      });
      setMsg("Medición registrada");
      setValorPosterior("");
      setEvidencia("");
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al registrar medición");
    }
  }

  async function onValidate(medicionId: string) {
    if (!lineaBaseId) return;
    try {
      await validateLineaBaseMedicion(lineaBaseId, medicionId);
      setMsg("Medición validada — impacto congelado");
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al validar");
    }
  }

  async function onAtribuir(medicionId: string, nivel: string) {
    if (!lineaBaseId) return;
    try {
      await updateLineaBaseAtribucion(lineaBaseId, medicionId, {
        atribucion_nivel: nivel,
        justificacion: "Atribución manual desde UI",
        evidencia: { fuente: "ui" },
      });
      setMsg("Atribución actualizada");
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error en atribución");
    }
  }

  if (loading) {
    return <div className="ops-page"><p className="muted">Cargando línea base…</p></div>;
  }

  if (!data) {
    return (
      <div className="ops-page">
        <p className="error">{error ?? "Línea base no encontrada"}</p>
        <Link to="/lineas-base">← Volver</Link>
      </div>
    );
  }

  const lb = data.linea_base;

  return (
    <div className="ops-page">
      <header className="page-header compact">
        <p><Link to="/lineas-base">← Líneas base</Link></p>
        <h1>{lb.indicador}</h1>
        <p className="muted">{lb.descripcion ?? "Sin descripción"} · Estado: {lb.estado}</p>
      </header>

      {error && <p className="error">{error}</p>}
      {msg && <p className="success">{msg}</p>}

      <section className="panel compact-panel">
        <h2 className="section-title">Línea base</h2>
        <dl className="detail-grid">
          <dt>Valor base</dt><dd>{lb.valor_base} {lb.unidad}</dd>
          <dt>Periodo base</dt><dd>{new Date(lb.fecha_inicio_base).toLocaleDateString("es-CO")} — {new Date(lb.fecha_fin_base).toLocaleDateString("es-CO")}</dd>
          <dt>Impacto esperado</dt><dd>{lb.impacto_esperado ?? "—"}</dd>
          <dt>Dirección</dt><dd>{lb.direccion_indicador}</dd>
          <dt>Oportunidad</dt><dd>{lb.opportunity_id ? <Link to={`/oportunidades/${lb.opportunity_id}`}>{lb.opportunity_id}</Link> : "—"}</dd>
          <dt>Plan</dt><dd>{lb.work_plan_id ? <Link to={`/operaciones/${lb.work_plan_id}`}>{lb.work_plan_id}</Link> : "—"}</dd>
        </dl>
      </section>

      {has("linea_base.manage") && lb.estado !== "CERRADA" && (
        <section className="panel compact-panel">
          <form className="compact-form" onSubmit={onAddMedicion}>
            <h3 className="section-title">Registrar medición posterior</h3>
            <label>Valor posterior<input type="number" value={valorPosterior} onChange={(e) => setValorPosterior(e.target.value)} required /></label>
            <label>Inicio periodo<input type="date" value={periodoInicio} onChange={(e) => setPeriodoInicio(e.target.value)} required /></label>
            <label>Fin periodo<input type="date" value={periodoFin} onChange={(e) => setPeriodoFin(e.target.value)} required /></label>
            <label>Evidencia (texto)<textarea value={evidencia} onChange={(e) => setEvidencia(e.target.value)} rows={2} /></label>
            <button type="submit">Registrar medición</button>
          </form>
        </section>
      )}

      <section className="panel compact-panel stack-gap">
        <h2 className="section-title">Comparación y evolución</h2>
        {data.mediciones.length === 0 && <p className="muted">Sin mediciones posteriores.</p>}
        {data.mediciones.map((med) => (
          <div key={med.id} className="approval-card">
            <p><strong>Medición {new Date(med.periodo_fin).toLocaleDateString("es-CO")}</strong> · {med.estado}</p>
            <p>Valor posterior: <strong>{med.valor_posterior}</strong></p>
            {med.impacto && (
              <dl className="detail-grid">
                <dt>Variación absoluta</dt><dd>{med.impacto.variacion_absoluta}</dd>
                <dt>Variación %</dt><dd>{med.impacto.variacion_porcentual != null ? `${med.impacto.variacion_porcentual.toFixed(2)}%` : "—"}</dd>
                <dt>Evaluación</dt><dd>{EVAL_LABELS[med.impacto.evaluacion] ?? med.impacto.evaluacion}</dd>
                <dt>Tipo impacto</dt><dd>{TIPO_IMPACTO_LABELS[med.impacto.tipo_impacto] ?? med.impacto.tipo_impacto}</dd>
                <dt>Impacto esperado</dt><dd>{med.impacto.impacto_esperado ?? lb.impacto_esperado ?? "—"}</dd>
                <dt>Impacto real</dt><dd>{med.impacto.impacto_real ?? "—"}</dd>
                <dt>Atribución</dt><dd>{med.impacto.atribucion_nivel}</dd>
              </dl>
            )}
            {has("linea_base.validate") && med.estado !== "VALIDADA" && med.impacto && !med.impacto.congelado && (
              <div className="toolbar compact-toolbar">
                <button type="button" onClick={() => onValidate(med.id)}>Validar medición</button>
                <button type="button" className="btn-secondary" onClick={() => onAtribuir(med.id, "PARCIALMENTE_ATRIBUIBLE")}>Atribución parcial</button>
                <button type="button" className="btn-secondary" onClick={() => onAtribuir(med.id, "ATRIBUIBLE")}>Atribuir</button>
              </div>
            )}
          </div>
        ))}
        {data.evolucion.puntos.length > 0 && (
          <table className="data-table compact-table">
            <thead><tr><th>Fecha</th><th>Valor</th><th>Evaluación</th><th>Estado</th></tr></thead>
            <tbody>
              {data.evolucion.puntos.map((p, i) => (
                <tr key={i}>
                  <td>{p.fecha ? new Date(p.fecha).toLocaleDateString("es-CO") : "—"}</td>
                  <td>{p.valor}</td>
                  <td>{p.evaluacion ? (EVAL_LABELS[p.evaluacion] ?? p.evaluacion) : "—"}</td>
                  <td>{p.estado}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="panel compact-panel">
        <h2 className="section-title">Historial y trazabilidad</h2>
        <table className="data-table compact-table">
          <thead><tr><th>Fecha</th><th>Acción</th><th>Actor</th></tr></thead>
          <tbody>
            {data.historial.map((h) => (
              <tr key={h.id}>
                <td>{h.fecha ? new Date(h.fecha).toLocaleString("es-CO") : "—"}</td>
                <td>{h.accion}</td>
                <td>{h.actor_id ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
