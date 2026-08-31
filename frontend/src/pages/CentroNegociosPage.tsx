import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  fetchCentroNegociosDashboard,
  fetchCentroNegociosPipeline,
  type CentroNegociosDashboard,
  type CentroNegociosPipelineItem,
} from "../api";
import { usePermissions } from "../hooks/usePermissions";

const ESTADO_LABELS: Record<string, string> = {
  BORRADOR: "Borrador",
  EN_REVISION: "En revisión",
  APROBADA: "Aprobada internamente",
  ENVIADA: "Presentada",
  ACEPTADA: "Contratada",
  RECHAZADA: "Descartada",
  VENCIDA: "Suspendida",
};

export function CentroNegociosPage() {
  const { has } = usePermissions();
  const [dashboard, setDashboard] = useState<CentroNegociosDashboard | null>(null);
  const [pipeline, setPipeline] = useState<CentroNegociosPipelineItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    Promise.all([fetchCentroNegociosDashboard(), fetchCentroNegociosPipeline()])
      .then(([d, p]) => {
        setDashboard(d);
        setPipeline(p);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar"))
      .finally(() => setLoading(false));
  }, []);

  const filtered = pipeline.filter(
    (p) =>
      !filter ||
      p.codigo.toLowerCase().includes(filter.toLowerCase()) ||
      p.titulo.toLowerCase().includes(filter.toLowerCase()),
  );

  return (
    <div className="ops-page">
      <header className="ops-header">
        <h1>Centro de Negocios</h1>
        <p className="muted">
          Oportunidades, propuestas, negociación y contratación — desde evaluación hasta implementación.
        </p>
        <div className="ops-actions">
          <Link to="/evaluaciones" className="btn">Evaluaciones →</Link>
          <Link to="/oportunidades" className="btn">Oportunidades →</Link>
          <Link to="/comercial" className="btn">Comercial y valor →</Link>
        </div>
      </header>

      {error && <p className="error-text">{error}</p>}
      {loading ? (
        <p>Cargando…</p>
      ) : (
        <>
          {dashboard && (
            <section className="panel compact-panel stats-row">
              <div className="stat-chip">
                <span className="stat-label">Oportunidades</span>
                <strong>{dashboard.oportunidades_total}</strong>
              </div>
              <div className="stat-chip">
                <span className="stat-label">Propuestas activas</span>
                <strong>{dashboard.propuestas_activas}</strong>
              </div>
              <div className="stat-chip">
                <span className="stat-label">Negociaciones abiertas</span>
                <strong>{dashboard.negociaciones_abiertas}</strong>
              </div>
              <div className="stat-chip">
                <span className="stat-label">Contrataciones</span>
                <strong>{dashboard.contrataciones}</strong>
              </div>
              {dashboard.valores && (
                <div className="stat-chip">
                  <span className="stat-label">Valor realizado</span>
                  <strong>{dashboard.valores.valor_realizado?.toLocaleString("es-CO") ?? "—"}</strong>
                </div>
              )}
            </section>
          )}

          <section className="panel compact-panel">
            <div className="panel-header-row">
              <h2>Pipeline comercial</h2>
              <input
                type="search"
                placeholder="Buscar propuesta…"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="search-input"
              />
            </div>
            <table className="data-table compact-table">
              <thead>
                <tr>
                  <th>Código</th>
                  <th>Título</th>
                  <th>Estado</th>
                  <th>Precio</th>
                  <th>Versión</th>
                  <th>Próximo paso</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="muted">
                      Sin propuestas en el pipeline. Cree una desde una evaluación EIAAX.
                    </td>
                  </tr>
                ) : (
                  filtered.map((p) => (
                    <tr key={p.id}>
                      <td>{p.codigo}</td>
                      <td>{p.titulo}</td>
                      <td>{ESTADO_LABELS[p.estado] ?? p.estado}</td>
                      <td>{p.precio_final != null ? p.precio_final.toLocaleString("es-CO") : "—"}</td>
                      <td>v{p.version}</td>
                      <td className="truncate-cell">{p.proximo_paso ?? "—"}</td>
                      <td>
                        <Link to={`/comercial/propuestas/${p.id}`} className="btn small">
                          Ver
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </section>

          {dashboard?.nota_potencial && (
            <p className="muted small-note">{dashboard.nota_potencial}</p>
          )}

          {!has("negocio.manage") && (
            <p className="muted">Solo lectura — requiere permisos de gestión para operar el ciclo comercial.</p>
          )}
        </>
      )}
    </div>
  );
}
