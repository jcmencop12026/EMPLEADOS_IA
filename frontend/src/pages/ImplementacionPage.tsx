import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  createImplProyecto,
  fetchImplProyectoDetalle,
  fetchImplProyectos,
  fetchImplTablero,
  type ImplProyectoSummary,
  type ImplTablero,
} from "../api";
import { usePermissions } from "../hooks/usePermissions";

export function ImplementacionPage() {
  const { has } = usePermissions();
  const [proyectos, setProyectos] = useState<ImplProyectoSummary[]>([]);
  const [selected, setSelected] = useState<ImplTablero | null>(null);
  const [loading, setLoading] = useState(true);
  const [titulo, setTitulo] = useState("");

  useEffect(() => {
    fetchImplProyectos()
      .then(setProyectos)
      .finally(() => setLoading(false));
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    const p = await createImplProyecto({ titulo });
    window.location.href = `/implementacion/${p.id}`;
  }

  async function onSelect(id: string) {
    setSelected(await fetchImplTablero(id));
  }

  return (
    <div className="ops-page">
      <header className="ops-header">
        <h1>Implementación y éxito del cliente</h1>
        <p>De propuesta aceptada a valor real generado.</p>
      </header>
      {loading ? (
        <p>Cargando…</p>
      ) : (
        <>
          {has("implementacion.manage") && (
            <form onSubmit={onCreate} className="inline-form">
              <input placeholder="Título del proyecto" value={titulo} onChange={(e) => setTitulo(e.target.value)} required />
              <button type="submit">Nueva implementación</button>
            </form>
          )}
          <section className="panel">
            <h2>Proyectos ({proyectos.length})</h2>
            <ul>
              {proyectos.map((p) => (
                <li key={p.id}>
                  <Link to={`/implementacion/${p.id}`}>{p.codigo} — {p.titulo}</Link>
                  <span> ({p.estado}, {p.avance_pct}%)</span>
                  <button type="button" onClick={() => onSelect(p.id)}>Tablero</button>
                </li>
              ))}
            </ul>
          </section>
          {selected && (
            <section className="panel">
              <h2>Tablero — {selected.proyecto?.codigo}</h2>
              <p>Fase: {selected.fase_actual} | Avance: {selected.avance_pct}%</p>
              {selected.salud && <p>Salud: {selected.salud.resultado} ({selected.salud.puntuacion})</p>}
              {selected.tco && <p>TCO: {selected.tco.total?.toLocaleString("es-CO")}</p>}
              {selected.bloqueadores && selected.bloqueadores.length > 0 && (
                <div className="alert-box">
                  <h3>Bloqueadores</h3>
                  {selected.bloqueadores.map((b, i) => (
                    <p key={i}>{b.descripcion}</p>
                  ))}
                </div>
              )}
            </section>
          )}
        </>
      )}
    </div>
  );
}
