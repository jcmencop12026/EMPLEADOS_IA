import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import type { OptimizacionRecomendacion } from "../api";
import {
  crearRecomendacionOptimizacion,
  fetchOptimizacionRecomendaciones,
  simularOptimizacion,
} from "../api";
import { HelpTooltip } from "../components/optimizacion/HelpTooltip";
import { EstadoBadge } from "../components/optimizacion/EstadoBadge";
import { SemanticBadge } from "../components/optimizacion/SemanticBadge";
import { labelEstadoEjecucion, TOOLTIPS } from "../lib/optimizacionLabels";

export function OptimizacionPage() {
  const [items, setItems] = useState<OptimizacionRecomendacion[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [presupuesto, setPresupuesto] = useState("100000000");
  const [objetivo, setObjetivo] = useState("MAXIMIZAR_VALOR");
  const [simResult, setSimResult] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState(false);
  const [estadoFilter, setEstadoFilter] = useState("");
  const [q, setQ] = useState("");

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

  const filtrados = useMemo(() => {
    return items.filter((r) => {
      if (estadoFilter && r.estado !== estadoFilter) return false;
      if (!q) return true;
      const hay = `${r.codigo} ${r.id} ${r.ejecucion?.correlation_id ?? ""}`.toLowerCase();
      return hay.includes(q.toLowerCase());
    });
  }, [items, estadoFilter, q]);

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
      <header className="page-header compact">
        <div>
          <h1>Optimización y recomendaciones</h1>
          <p className="muted">
            Portafolio óptimo bajo restricciones.
            <SemanticBadge kind="RECOMENDACION" />
            <HelpTooltip text={TOOLTIPS.recomendacion} />
          </p>
        </div>
      </header>

      {error && <div className="alert alert-error">{error}</div>}

      <section className="card compact-panel" style={{ marginBottom: "1rem" }}>
        <h2>Simulador</h2>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
          <select value={objetivo} onChange={(e) => setObjetivo(e.target.value)}>
            <option value="MAXIMIZAR_VALOR">Maximizar valor</option>
            <option value="MAXIMIZAR_ROI">Maximizar ROI</option>
            <option value="MAXIMIZAR_IMPACTO">Maximizar impacto</option>
            <option value="MINIMIZAR_RIESGO">Minimizar riesgo</option>
            <option value="RESULTADO_EQUILIBRADO">Resultado equilibrado</option>
          </select>
          <input type="number" value={presupuesto} onChange={(e) => setPresupuesto(e.target.value)} placeholder="Presupuesto máximo" />
          <button type="button" className="btn btn-primary btn-sm" onClick={onSimular} disabled={busy}>Simular</button>
          {simResult && (
            <button type="button" className="btn btn-sm" onClick={onGuardar} disabled={busy}>Guardar recomendación</button>
          )}
        </div>
        {simResult && (
          <div>
            <p><strong>{simResult.factible ? "Solución factible" : "Sin solución factible"}</strong></p>
            {!simResult.factible && <p className="muted">{(simResult.conflictos as string[])?.join("; ")}</p>}
            <pre className="compact-pre">{JSON.stringify(simResult.explicacion, null, 2)}</pre>
          </div>
        )}
      </section>

      <section className="card compact-panel">
        <div className="panel-header-row">
          <h2>Recomendaciones</h2>
          <div style={{ display: "flex", gap: 8 }}>
            <input className="filter-input" placeholder="Buscar…" value={q} onChange={(e) => setQ(e.target.value)} />
            <select value={estadoFilter} onChange={(e) => setEstadoFilter(e.target.value)}>
              <option value="">Todos</option>
              <option value="PROPUESTA">Propuesta</option>
              <option value="APROBADA">Aprobada</option>
              <option value="EJECUTADA">Ejecutada</option>
              <option value="FALLIDA">Fallida</option>
              <option value="RECHAZADA">Rechazada</option>
              <option value="CANCELADA">Cancelada</option>
            </select>
          </div>
        </div>
        {loading ? (
          <p className="muted">Cargando…</p>
        ) : filtrados.length === 0 ? (
          <p className="muted">Sin recomendaciones.</p>
        ) : (
          <table className="data-table compact-table">
            <thead>
              <tr>
                <th>Código</th>
                <th>Estado</th>
                <th>Ejecución</th>
                <th>Objetivo</th>
                <th>Valor</th>
                <th>ROI</th>
                <th>Riesgo</th>
                <th>Correlation</th>
              </tr>
            </thead>
            <tbody>
              {filtrados.map((r) => (
                <tr key={r.id}>
                  <td><Link to={`/optimizacion/${r.id}`}>{r.codigo}</Link></td>
                  <td><EstadoBadge estado={r.estado} /></td>
                  <td>{labelEstadoEjecucion(r.ejecucion?.estado)}</td>
                  <td>{r.objetivo}</td>
                  <td>{r.valor_esperado_total?.toLocaleString("es-CO")}</td>
                  <td>{r.roi_esperado != null ? r.roi_esperado.toFixed(2) : "—"}</td>
                  <td>{r.riesgo_promedio != null ? r.riesgo_promedio.toFixed(2) : "—"}</td>
                  <td className="mono">{r.ejecucion?.correlation_id?.slice(0, 10) ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
