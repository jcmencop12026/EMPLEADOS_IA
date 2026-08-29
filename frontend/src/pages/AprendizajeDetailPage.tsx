import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import type { RecalibracionItem } from "../api";
import {
  aplicarRecalibracion,
  aprobarRecalibracion,
  evaluarCicloAprendizaje,
  fetchCicloAprendizaje,
  fetchHistorialAprendizaje,
  rechazarRecalibracion,
} from "../api";

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
    return (
      <div className="page">
        <p className="muted">Cargando ciclo…</p>
      </div>
    );
  }

  const desviaciones = (detail.desviaciones ?? {}) as Record<string, { esperado?: number; real?: number; direccion?: string }>;

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="muted">
            <Link to="/aprendizaje">← Aprendizaje</Link>
          </p>
          <h1>Ciclo {detail.id.slice(0, 8)}…</h1>
          <p className="muted">
            Oportunidad{" "}
            <Link to={`/oportunidades/${detail.opportunity_id}`}>{detail.opportunity_id.slice(0, 8)}…</Link> — {detail.estado}
          </p>
        </div>
      </header>

      {error && <div className="alert alert-error">{error}</div>}

      <section className="card" style={{ marginBottom: "1rem" }}>
        <h2>Esperado vs real</h2>
        <table className="data-table">
          <thead>
            <tr>
              <th>Métrica</th>
              <th>Esperado</th>
              <th>Real</th>
              <th>Desviación</th>
            </tr>
          </thead>
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
                <td>{dev?.direccion ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {detail.estado === "ABIERTO" && (
          <div style={{ marginTop: "1rem", display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            <input
              type="number"
              placeholder="Valor real"
              value={valorReal}
              onChange={(e) => setValorReal(e.target.value)}
            />
            <input
              type="number"
              placeholder="Impacto real"
              value={impactoReal}
              onChange={(e) => setImpactoReal(e.target.value)}
            />
            <button type="button" className="btn btn-primary" onClick={onEvaluar} disabled={busy}>
              Evaluar ciclo
            </button>
          </div>
        )}
      </section>

      {detail.explicacion_prioridad && (
        <section className="card" style={{ marginBottom: "1rem" }}>
          <h2>Explicación de repriorización</h2>
          <p>Calidad recomendación: <strong>{detail.calidad_recomendacion}</strong></p>
          <p>Prioridad anterior: {detail.prioridad_anterior ?? "—"} → propuesta: {detail.prioridad_propuesta ?? "—"}</p>
          <pre style={{ whiteSpace: "pre-wrap", fontSize: "0.85rem" }}>
            {JSON.stringify(detail.explicacion_prioridad, null, 2)}
          </pre>
        </section>
      )}

      <section className="card" style={{ marginBottom: "1rem" }}>
        <h2>Recalibraciones</h2>
        {(detail.recalibraciones ?? []).length === 0 ? (
          <p className="muted">Sin propuestas de recalibración.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Campo</th>
                <th>Estado</th>
                <th>Anterior</th>
                <th>Nuevo</th>
                <th>Justificación</th>
                <th>Acciones</th>
              </tr>
            </thead>
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
                        <button type="button" className="btn btn-sm" onClick={() => onAprobar(rec)} disabled={busy}>
                          Aprobar
                        </button>{" "}
                        <button type="button" className="btn btn-sm" onClick={() => onRechazar(rec)} disabled={busy}>
                          Rechazar
                        </button>
                      </>
                    )}
                    {rec.estado === "APROBADA" && (
                      <button type="button" className="btn btn-sm btn-primary" onClick={() => onAplicar(rec)} disabled={busy}>
                        Aplicar
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="card">
        <h2>Historial auditable</h2>
        {historial.length === 0 ? (
          <p className="muted">Sin eventos.</p>
        ) : (
          <ul>
            {(historial as { accion: string; created_at?: string }[]).map((h, i) => (
              <li key={i}>
                {h.created_at ? new Date(h.created_at).toLocaleString("es-CO") : ""} — {h.accion}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
