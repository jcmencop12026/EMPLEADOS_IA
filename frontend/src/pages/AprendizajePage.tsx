import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { CicloAprendizajeItem, PatronAprendizajeItem } from "../api";
import { fetchCiclosAprendizaje, fetchPatronesAprendizaje } from "../api";

export function AprendizajePage() {
  const [ciclos, setCiclos] = useState<CicloAprendizajeItem[]>([]);
  const [patrones, setPatrones] = useState<PatronAprendizajeItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([fetchCiclosAprendizaje(), fetchPatronesAprendizaje()])
      .then(([c, p]) => {
        setCiclos(c);
        setPatrones(p);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar aprendizaje"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Aprendizaje y repriorización</h1>
          <p className="muted">
            Ciclo cerrado: señal → diagnóstico → oportunidad → ejecución → impacto → aprendizaje → nueva priorización.
          </p>
        </div>
      </header>

      {error && <div className="alert alert-error">{error}</div>}

      <section className="card" style={{ marginBottom: "1rem" }}>
        <h2>Ciclos de aprendizaje</h2>
        {loading ? (
          <p className="muted">Cargando…</p>
        ) : ciclos.length === 0 ? (
          <p className="muted">No hay ciclos registrados. Evalúe una oportunidad desde su detalle.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Oportunidad</th>
                <th>Estado</th>
                <th>Calidad</th>
                <th>Prioridad ant.</th>
                <th>Prioridad prop.</th>
                <th>Fecha</th>
              </tr>
            </thead>
            <tbody>
              {ciclos.map((c) => (
                <tr key={c.id}>
                  <td>
                    <Link to={`/aprendizaje/${c.id}`}>{c.id.slice(0, 8)}…</Link>
                  </td>
                  <td>
                    <Link to={`/oportunidades/${c.opportunity_id}`}>{c.opportunity_id.slice(0, 8)}…</Link>
                  </td>
                  <td>{c.estado}</td>
                  <td>{c.calidad_recomendacion ?? "—"}</td>
                  <td>{c.prioridad_anterior ?? "—"}</td>
                  <td>{c.prioridad_propuesta ?? "—"}</td>
                  <td>{c.created_at ? new Date(c.created_at).toLocaleString("es-CO") : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="card">
        <h2>Patrones detectados</h2>
        {patrones.length === 0 ? (
          <p className="muted">Sin patrones repetidos aún.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Tipo</th>
                <th>Dominio</th>
                <th>Resumen</th>
                <th>Ocurrencias</th>
              </tr>
            </thead>
            <tbody>
              {patrones.map((p) => (
                <tr key={p.id}>
                  <td>{p.tipo_patron}</td>
                  <td>{p.dominio ?? "—"}</td>
                  <td>{p.resumen}</td>
                  <td>{p.ocurrencias}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
