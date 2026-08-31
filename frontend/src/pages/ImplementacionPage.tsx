import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  createImplProyecto,
  fetchImplProyectos,
  fetchImplTablero,
  type ImplProyectoSummary,
  type ImplTablero,
} from "../api";
import { ImplementationCycleBar } from "../components/comercial/ImplementationCycleBar";
import { formatMoney } from "../lib/comercialLabels";
import { usePermissions } from "../hooks/usePermissions";

export function ImplementacionPage() {
  const { has } = usePermissions();
  const [proyectos, setProyectos] = useState<ImplProyectoSummary[]>([]);
  const [selected, setSelected] = useState<ImplTablero | null>(null);
  const [loading, setLoading] = useState(true);
  const [titulo, setTitulo] = useState("");
  const [filter, setFilter] = useState("");

  useEffect(() => {
    fetchImplProyectos().then(setProyectos).finally(() => setLoading(false));
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    const p = await createImplProyecto({ titulo });
    window.location.href = `/implementacion/${p.id}`;
  }

  async function onSelect(id: string) {
    setSelected(await fetchImplTablero(id));
  }

  const filtered = proyectos.filter(
    (p) => !filter || p.codigo.toLowerCase().includes(filter.toLowerCase()) || p.titulo.toLowerCase().includes(filter.toLowerCase()),
  );

  return (
    <div className="ops-page">
      <header className="ops-header">
        <h1>Implementación y seguimiento del valor</h1>
        <p className="muted">De propuesta aceptada a valor medido y éxito del cliente.</p>
        <Link to="/comercial" className="btn">Ver propuestas comerciales →</Link>
      </header>

      <section className="panel compact-panel">
        <h2>Ciclo de implementación</h2>
        <ImplementationCycleBar estado={selected?.fase_actual ?? "PLANIFICACION"} />
      </section>

      {loading ? <p>Cargando…</p> : (
        <>
          {has("implementacion.manage") && (
            <form onSubmit={onCreate} className="inline-form">
              <input placeholder="Título del proyecto" value={titulo} onChange={(e) => setTitulo(e.target.value)} required />
              <button type="submit" className="btn primary">Nueva implementación</button>
            </form>
          )}
          <section className="panel compact-panel">
            <h2>Proyectos ({filtered.length})</h2>
            <input className="ops-input filter-input" placeholder="Filtrar…" value={filter} onChange={(e) => setFilter(e.target.value)} />
            <table className="data-table compact-table">
              <thead><tr><th>Código</th><th>Título</th><th>Estado</th><th>Avance</th><th></th></tr></thead>
              <tbody>
                {filtered.map((p) => (
                  <tr key={p.id}>
                    <td><Link to={`/implementacion/${p.id}`}>{p.codigo}</Link></td>
                    <td>{p.titulo}</td>
                    <td>{p.estado}</td>
                    <td>{p.avance_pct}%</td>
                    <td><button type="button" className="btn link" onClick={() => onSelect(p.id)}>Tablero</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
          {selected && (
            <section className="panel compact-panel">
              <h2>Tablero — {selected.proyecto?.codigo}</h2>
              <ImplementationCycleBar estado={selected.fase_actual} />
              <div className="metrics-grid compact-metrics">
                <div><strong>Fase</strong><span>{selected.fase_actual}</span></div>
                <div><strong>Avance</strong><span>{selected.avance_pct}%</span></div>
                <div><strong>Valor esperado</strong><span>{typeof selected.valor_esperado === "object" ? JSON.stringify(selected.valor_esperado) : formatMoney(selected.valor_esperado as number)}</span></div>
                {selected.tco && <div><strong>TCO</strong><span>{formatMoney(selected.tco.total)}</span></div>}
                {selected.salud && <div><strong>Salud</strong><span>{selected.salud.resultado}</span></div>}
              </div>
              {selected.bloqueadores && selected.bloqueadores.length > 0 && (
                <div className="alert-box">
                  <h3>Bloqueadores</h3>
                  {selected.bloqueadores.map((b, i) => <p key={i}>{b.descripcion}</p>)}
                </div>
              )}
            </section>
          )}
        </>
      )}
    </div>
  );
}
