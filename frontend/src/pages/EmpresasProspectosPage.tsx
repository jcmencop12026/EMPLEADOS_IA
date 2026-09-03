import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { fetchEvaluaciones, type EvaluacionExpedienteSummary } from "../api";
import { EmptyState, ErrorState, LoadingState } from "../components/AsyncState";
import { usePageAssistantContext } from "../hooks/usePageAssistantContext";
import { CONFIANZA, ESTADO_EXPEDIENTE, label } from "../lib/evaluacionLabels";

type EntidadRow = {
  entidad_nombre: string;
  expediente: EvaluacionExpedienteSummary;
  total: number;
};

export function EmpresasProspectosPage() {
  const [items, setItems] = useState<EvaluacionExpedienteSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");

  usePageAssistantContext({ module: "empresas_prospectos" });

  useEffect(() => {
    setLoading(true);
    fetchEvaluaciones()
      .then((r) => { setItems(r.items); setError(null); })
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar"))
      .finally(() => setLoading(false));
  }, []);

  const entidades = useMemo(() => {
    const map = new Map<string, EntidadRow>();
    for (const item of items) {
      const key = item.entidad_nombre.trim() || "Sin nombre";
      const prev = map.get(key);
      if (!prev) {
        map.set(key, { entidad_nombre: key, expediente: item, total: 1 });
        continue;
      }
      prev.total += 1;
      const prevDate = new Date(prev.expediente.updated_at ?? prev.expediente.created_at ?? 0);
      const itemDate = new Date(item.updated_at ?? item.created_at ?? 0);
      if (itemDate >= prevDate) prev.expediente = item;
    }
    return Array.from(map.values()).sort((a, b) => a.entidad_nombre.localeCompare(b.entidad_nombre, "es"));
  }, [items]);

  const filtered = entidades.filter((e) => {
    const term = q.trim().toLowerCase();
    if (!term) return true;
    return (
      e.entidad_nombre.toLowerCase().includes(term)
      || e.expediente.codigo.toLowerCase().includes(term)
      || e.expediente.titulo.toLowerCase().includes(term)
    );
  });

  if (loading) return <LoadingState message="Cargando empresas y prospectos…" />;
  if (error && !items.length) return <ErrorState message={error} onRetry={() => window.location.reload()} />;

  return (
    <div className="ops-page empresas-page">
      <header className="page-header compact">
        <h1>Empresas y prospectos</h1>
        <p className="muted">
          Acceso operativo a evaluaciones, cabina y presentación sin recorrer menús técnicos.
        </p>
      </header>

      <div className="toolbar compact-toolbar">
        <input
          type="search"
          placeholder="Buscar empresa, código o evaluación…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <Link to="/evaluaciones" className="btn secondary">Ver todas las evaluaciones</Link>
      </div>

      {error && <p className="error">{error}</p>}

      {filtered.length === 0 ? (
        <EmptyState
          title="Sin empresas ni prospectos"
          message="Cree una evaluación EIAAX para registrar la primera entidad. Los expedientes aparecerán aquí con acceso directo a la cabina."
          action={<Link to="/evaluaciones" className="btn primary">Ir a evaluaciones</Link>}
        />
      ) : (
        <div className="panel compact-panel table-wrap">
          <table className="data-table compact-table empresas-table">
            <thead>
              <tr>
                <th>Entidad</th>
                <th>Evaluación activa</th>
                <th>Estado</th>
                <th>Info</th>
                <th>Confianza</th>
                <th>Expedientes</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((row) => {
                const exp = row.expediente;
                return (
                  <tr key={`${row.entidad_nombre}-${exp.id}`}>
                    <td><strong>{row.entidad_nombre}</strong></td>
                    <td>
                      <Link to={`/evaluaciones/${exp.id}`}>{exp.codigo}</Link>
                      <span className="muted small block">{exp.titulo}</span>
                    </td>
                    <td>{label(ESTADO_EXPEDIENTE, exp.estado)}</td>
                    <td>{exp.porcentaje_informacion}%</td>
                    <td>{label(CONFIANZA, exp.confianza_global)}</td>
                    <td>{row.total}</td>
                    <td className="actions-cell compact-actions">
                      <Link to={`/evaluaciones/${exp.id}`} className="btn small primary" title="Abrir cabina empresa">
                        Cabina
                      </Link>
                      <Link to={`/centro-control?expediente=${exp.id}`} className="btn small secondary" title="Centro de empresa">
                        Centro
                      </Link>
                      <Link to={`/presentacion/${exp.id}`} className="btn small secondary" title="Modo presentación">
                        Presentar
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
