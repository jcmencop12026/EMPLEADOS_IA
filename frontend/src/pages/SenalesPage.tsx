import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { SignalItem, SignalSourceItem } from "../api";
import { fetchRecentSignals, fetchSignalSources } from "../api";

const MODO_LABELS: Record<string, string> = {
  REAL: "Real",
  SINTETICO: "Sintético (prueba)",
  PRUEBA: "Prueba",
};

const ESTADO_LABELS: Record<string, string> = {
  RECIBIDA: "Recibida",
  PROCESADA: "Procesada",
  RECHAZADA: "Rechazada",
  DUPLICADA: "Duplicada",
};

export function SenalesPage() {
  const [sources, setSources] = useState<SignalSourceItem[]>([]);
  const [signals, setSignals] = useState<SignalItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [filtroModo, setFiltroModo] = useState("");

  useEffect(() => {
    Promise.all([fetchSignalSources(), fetchRecentSignals(filtroModo || undefined)])
      .then(([src, sig]) => {
        setSources(src);
        setSignals(sig);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar señales"));
  }, [filtroModo]);

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Señales y fuentes</h1>
          <p className="muted">
            Consulta fuentes parametrizables, señales recientes y su estado de procesamiento hacia oportunidades.
          </p>
        </div>
      </header>

      {error && <div className="alert alert-error">{error}</div>}

      <section className="card" style={{ marginBottom: "1.5rem" }}>
        <h2>Fuentes de datos</h2>
        {sources.length === 0 ? (
          <p className="muted">No hay fuentes registradas para esta empresa.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Código</th>
                <th>Nombre</th>
                <th>Tipo</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {sources.map((s) => (
                <tr key={s.id}>
                  <td>{s.code}</td>
                  <td>{s.name}</td>
                  <td>{s.tipo_fuente}</td>
                  <td>{s.is_active ? "Activa" : "Inactiva"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="card">
        <div className="toolbar" style={{ marginBottom: "1rem" }}>
          <h2>Señales recientes</h2>
          <label>
            Modo{" "}
            <select value={filtroModo} onChange={(e) => setFiltroModo(e.target.value)}>
              <option value="">Todos</option>
              <option value="REAL">Real</option>
              <option value="SINTETICO">Sintético</option>
              <option value="PRUEBA">Prueba</option>
            </select>
          </label>
        </div>
        {signals.length === 0 ? (
          <p className="muted">No hay señales registradas.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Tipo</th>
                <th>Origen</th>
                <th>Modo</th>
                <th>Métrica</th>
                <th>Estado</th>
                <th>Referencia</th>
              </tr>
            </thead>
            <tbody>
              {signals.map((s) => (
                <tr key={s.id}>
                  <td>{s.signal_at ? new Date(s.signal_at).toLocaleString("es-CO") : "—"}</td>
                  <td>{s.tipo}</td>
                  <td>{s.origen}</td>
                  <td>{MODO_LABELS[s.modo_ingesta] ?? s.modo_ingesta}</td>
                  <td>
                    {s.metrica ?? "—"}
                    {s.valor_metrica ? ` (${s.valor_metrica}${s.unidad ? ` ${s.unidad}` : ""})` : ""}
                  </td>
                  <td>{ESTADO_LABELS[s.estado_procesamiento] ?? s.estado_procesamiento}</td>
                  <td>
                    <Link to={`/senales/${s.id}`}>{s.referencia ?? s.id.slice(0, 8)}</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <p className="muted" style={{ marginTop: "1rem" }}>
          Las oportunidades originadas desde señales reales se gestionan en{" "}
          <Link to="/oportunidades">Centro de oportunidades</Link>.
        </p>
      </section>
    </div>
  );
}
