import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import type { CicloAprendizajeItem, PatronAprendizajeItem, RecalibracionItem } from "../api";
import { fetchCiclosAprendizaje, fetchPatronesAprendizaje, fetchRecalibraciones } from "../api";
import { HelpTooltip } from "../components/optimizacion/HelpTooltip";
import { EstadoBadge } from "../components/optimizacion/EstadoBadge";
import { SemanticBadge } from "../components/optimizacion/SemanticBadge";
import { extractCorrelationId, sinCambioPrioridad, TOOLTIPS } from "../lib/optimizacionLabels";

export function AprendizajePage() {
  const [ciclos, setCiclos] = useState<CicloAprendizajeItem[]>([]);
  const [patrones, setPatrones] = useState<PatronAprendizajeItem[]>([]);
  const [recalibraciones, setRecalibraciones] = useState<RecalibracionItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"ciclos" | "repriorizacion" | "patrones">("ciclos");
  const [q, setQ] = useState("");
  const [estadoFilter, setEstadoFilter] = useState("");

  useEffect(() => {
    Promise.all([fetchCiclosAprendizaje(), fetchPatronesAprendizaje(), fetchRecalibraciones()])
      .then(([c, p, r]) => {
        setCiclos(c);
        setPatrones(p);
        setRecalibraciones(r);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar aprendizaje"))
      .finally(() => setLoading(false));
  }, []);

  const ciclosFiltrados = useMemo(() => {
    return ciclos.filter((c) => {
      if (estadoFilter && c.estado !== estadoFilter) return false;
      if (!q) return true;
      const hay = `${c.id} ${c.opportunity_id} ${extractCorrelationId(c.referencias) ?? ""}`.toLowerCase();
      return hay.includes(q.toLowerCase());
    });
  }, [ciclos, q, estadoFilter]);

  return (
    <div className="page">
      <header className="page-header compact">
        <div>
          <h1>Aprendizaje y repriorización</h1>
          <p className="muted">
            Qué aprendió el sistema, de qué resultado provino y qué cambiaría a futuro.
            <HelpTooltip text={TOOLTIPS.aprendizaje} />
          </p>
        </div>
        <div className="toolbar compact-tabs">
          {(["ciclos", "repriorizacion", "patrones"] as const).map((t) => (
            <button key={t} type="button" className={tab === t ? "btn btn-primary btn-sm" : "btn btn-sm"} onClick={() => setTab(t)}>
              {t === "ciclos" ? "Aprendizajes" : t === "repriorizacion" ? "Repriorización" : "Patrones"}
            </button>
          ))}
        </div>
      </header>

      {error && <div className="alert alert-error">{error}</div>}

      {tab === "ciclos" && (
        <section className="card compact-panel">
          <div className="panel-header-row">
            <h2>Ciclos de aprendizaje</h2>
            <div style={{ display: "flex", gap: 8 }}>
              <input className="filter-input" placeholder="Buscar…" value={q} onChange={(e) => setQ(e.target.value)} />
              <select value={estadoFilter} onChange={(e) => setEstadoFilter(e.target.value)}>
                <option value="">Todos los estados</option>
                <option value="ABIERTO">Abierto</option>
                <option value="EVALUADO">Evaluado</option>
                <option value="CERRADO">Cerrado</option>
              </select>
            </div>
          </div>
          {loading ? (
            <p className="muted">Cargando…</p>
          ) : ciclosFiltrados.length === 0 ? (
            <p className="muted">No hay ciclos registrados.</p>
          ) : (
            <table className="data-table compact-table">
              <thead>
                <tr>
                  <th>Ciclo</th>
                  <th>Oportunidad</th>
                  <th>Estado</th>
                  <th>Esperado / Real (valor)</th>
                  <th>Repriorización</th>
                  <th>Correlation</th>
                  <th>Fecha</th>
                </tr>
              </thead>
              <tbody>
                {ciclosFiltrados.map((c) => {
                  const sinCambio = sinCambioPrioridad(c.prioridad_anterior, c.prioridad_propuesta);
                  return (
                    <tr key={c.id}>
                      <td><Link to={`/aprendizaje/${c.id}`}>{c.id.slice(0, 8)}…</Link></td>
                      <td><Link to={`/oportunidades/${c.opportunity_id}`}>{c.opportunity_id.slice(0, 8)}…</Link></td>
                      <td><EstadoBadge estado={c.estado} /></td>
                      <td>{c.valor_esperado ?? "—"} / {c.valor_real ?? "—"}</td>
                      <td>
                        {sinCambio ? (
                          <span className="muted">Sin cambio</span>
                        ) : (
                          <>{c.prioridad_anterior ?? "—"} → {c.prioridad_propuesta ?? "—"}</>
                        )}
                      </td>
                      <td className="mono">{extractCorrelationId(c.referencias)?.slice(0, 10) ?? "—"}</td>
                      <td>{c.created_at ? new Date(c.created_at).toLocaleString("es-CO") : "—"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </section>
      )}

      {tab === "repriorizacion" && (
        <section className="card compact-panel">
          <h2>
            Repriorización
            <HelpTooltip text={TOOLTIPS.repriorizacion} />
          </h2>
          {recalibraciones.length === 0 ? (
            <p className="muted">No hubo cambios de prioridad sugeridos.</p>
          ) : (
            <table className="data-table compact-table">
              <thead>
                <tr>
                  <th>Campo</th>
                  <th>Anterior</th>
                  <th>Nuevo</th>
                  <th>Estado</th>
                  <th>Motivo</th>
                  <th>Ciclo</th>
                </tr>
              </thead>
              <tbody>
                {recalibraciones.map((r) => (
                  <tr key={r.id}>
                    <td>{r.campo}</td>
                    <td>{r.valor_anterior ?? "—"}</td>
                    <td>{r.valor_nuevo ?? "—"}</td>
                    <td>{r.estado}</td>
                    <td>{r.justificacion}</td>
                    <td><Link to={`/aprendizaje/${r.ciclo_id}`}>{r.ciclo_id.slice(0, 8)}…</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}

      {tab === "patrones" && (
        <section className="card compact-panel">
          <h2>Patrones detectados <SemanticBadge kind="INFERENCIA" /></h2>
          {patrones.length === 0 ? (
            <p className="muted">Sin patrones repetidos aún.</p>
          ) : (
            <table className="data-table compact-table">
              <thead>
                <tr><th>Tipo</th><th>Dominio</th><th>Resumen</th><th>Ocurrencias</th><th>Última detección</th></tr>
              </thead>
              <tbody>
                {patrones.map((p) => (
                  <tr key={p.id}>
                    <td>{p.tipo_patron}</td>
                    <td>{p.dominio ?? "—"}</td>
                    <td>{p.resumen}</td>
                    <td>{p.ocurrencias}</td>
                    <td>—</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}
    </div>
  );
}
