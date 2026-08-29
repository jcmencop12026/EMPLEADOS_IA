import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { OptimizacionRecomendacion } from "../api";
import {
  crearRecomendacionOptimizacion,
  fetchOptimizacionRecomendaciones,
  simularOptimizacion,
} from "../api";

export function OptimizacionPage() {
  const [items, setItems] = useState<OptimizacionRecomendacion[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [presupuesto, setPresupuesto] = useState("100000000");
  const [objetivo, setObjetivo] = useState("MAXIMIZAR_VALOR");
  const [simResult, setSimResult] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState(false);

  function load() {
    setLoading(true);
    fetchOptimizacionRecomendaciones()
      .then(setItems)
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar"))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
  }, []);

  async function onSimular() {
    setBusy(true);
    setError(null);
    try {
      const res = (await simularOptimizacion({
        objetivo,
        restricciones: { presupuesto_maximo: Number(presupuesto), max_iniciativas: 3 },
      })) as Record<string, unknown>;
      setSimResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error en simulación");
    } finally {
      setBusy(false);
    }
  }

  async function onGuardar() {
    setBusy(true);
    try {
      await crearRecomendacionOptimizacion({
        objetivo,
        restricciones: { presupuesto_maximo: Number(presupuesto), max_iniciativas: 3 },
      });
      setSimResult(null);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al guardar");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Optimización y recomendaciones</h1>
          <p className="muted">¿Qué conviene hacer primero y por qué? Portafolio óptimo bajo restricciones.</p>
        </div>
      </header>

      {error && <div className="alert alert-error">{error}</div>}

      <section className="card" style={{ marginBottom: "1rem" }}>
        <h2>Simulador</h2>
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginBottom: "0.5rem" }}>
          <select value={objetivo} onChange={(e) => setObjetivo(e.target.value)}>
            <option value="MAXIMIZAR_VALOR">Maximizar valor</option>
            <option value="MAXIMIZAR_ROI">Maximizar ROI</option>
            <option value="MAXIMIZAR_IMPACTO">Maximizar impacto</option>
            <option value="MINIMIZAR_RIESGO">Minimizar riesgo</option>
            <option value="RESULTADO_EQUILIBRADO">Resultado equilibrado</option>
          </select>
          <input
            type="number"
            value={presupuesto}
            onChange={(e) => setPresupuesto(e.target.value)}
            placeholder="Presupuesto máximo"
          />
          <button type="button" className="btn btn-primary" onClick={onSimular} disabled={busy}>
            Simular
          </button>
          {simResult && (
            <button type="button" className="btn" onClick={onGuardar} disabled={busy}>
              Guardar recomendación
            </button>
          )}
        </div>
        {simResult && (
          <div>
            <p>
              <strong>{simResult.factible ? "Solución factible" : "Sin solución factible"}</strong>
            </p>
            {!simResult.factible && (
              <p className="muted">{(simResult.conflictos as string[])?.join("; ")}</p>
            )}
            {Boolean(simResult.seleccion) && (
              <p>Selección: {(simResult.seleccion as string[]).length} iniciativas</p>
            )}
            <pre style={{ fontSize: "0.8rem", whiteSpace: "pre-wrap" }}>
              {JSON.stringify(simResult.explicacion, null, 2)}
            </pre>
          </div>
        )}
      </section>

      <section className="card">
        <h2>Recomendaciones guardadas</h2>
        {loading ? (
          <p className="muted">Cargando…</p>
        ) : items.length === 0 ? (
          <p className="muted">Sin recomendaciones. Use el simulador para generar una.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Código</th>
                <th>Objetivo</th>
                <th>Estado</th>
                <th>Factible</th>
                <th>Valor</th>
                <th>Costo</th>
                <th>ROI</th>
              </tr>
            </thead>
            <tbody>
              {items.map((r) => (
                <tr key={r.id}>
                  <td>
                    <Link to={`/optimizacion/${r.id}`}>{r.codigo}</Link>
                  </td>
                  <td>{r.objetivo}</td>
                  <td>{r.estado}</td>
                  <td>{r.factible ? "Sí" : "No"}</td>
                  <td>{r.valor_esperado_total?.toLocaleString("es-CO")}</td>
                  <td>{r.costo_esperado_total?.toLocaleString("es-CO")}</td>
                  <td>{r.roi_esperado != null ? r.roi_esperado.toFixed(2) : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
