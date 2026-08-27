import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { OpportunityItem, OpportunitySummary } from "../api";
import { fetchOpportunities, fetchOpportunitySummary } from "../api";

const COLUMNAS = [
  { key: "codigo", label: "Código" },
  { key: "titulo", label: "Oportunidad" },
  { key: "tipo", label: "Tipo" },
  { key: "dominio", label: "Dominio" },
  { key: "estado", label: "Estado" },
  { key: "prioridad_score", label: "Prioridad" },
  { key: "valor_potencial", label: "Valor potencial" },
  { key: "valor_materializado", label: "Valor materializado" },
  { key: "confianza", label: "Confianza" },
  { key: "pertinencia", label: "Pertinencia" },
  { key: "momento", label: "Momento" },
  { key: "fecha_deteccion", label: "Fecha" },
] as const;

const COLS_KEY = "oportunidades_cols";

function loadVisibleCols(): Set<string> {
  try {
    const raw = localStorage.getItem(COLS_KEY);
    if (raw) return new Set(JSON.parse(raw) as string[]);
  } catch { /* ignore */ }
  return new Set(COLUMNAS.map((c) => c.key));
}

function formatMoney(v: number | null): string {
  if (v == null) return "—";
  return new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(v);
}

export function OportunidadesPage() {
  const [items, setItems] = useState<OpportunityItem[]>([]);
  const [summary, setSummary] = useState<OpportunitySummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filtroEstado, setFiltroEstado] = useState("");
  const [filtroDominio, setFiltroDominio] = useState("");
  const [busqueda, setBusqueda] = useState("");
  const [visibleCols, setVisibleCols] = useState<Set<string>>(loadVisibleCols);

  useEffect(() => {
    localStorage.setItem(COLS_KEY, JSON.stringify([...visibleCols]));
  }, [visibleCols]);

  useEffect(() => {
    const params = new URLSearchParams();
    if (filtroEstado) params.set("estado", filtroEstado);
    if (filtroDominio) params.set("dominio", filtroDominio);
    if (busqueda) params.set("q", busqueda);
    Promise.all([
      fetchOpportunities(params.toString()),
      fetchOpportunitySummary(),
    ])
      .then(([list, sum]) => {
        setItems(list.items);
        setSummary(sum);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar oportunidades"));
  }, [filtroEstado, filtroDominio, busqueda]);

  function toggleCol(key: string) {
    setVisibleCols((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  function cellValue(item: OpportunityItem, key: string): string {
    switch (key) {
      case "valor_potencial":
      case "valor_materializado":
        return formatMoney(item[key as keyof OpportunityItem] as number | null);
      case "confianza":
      case "prioridad_score":
        return item[key as keyof OpportunityItem] != null
          ? Number(item[key as keyof OpportunityItem]).toFixed(2)
          : "—";
      case "fecha_deteccion":
        return item.fecha_deteccion ? new Date(item.fecha_deteccion).toLocaleDateString("es-CO") : "—";
      default:
        return String(item[key as keyof OpportunityItem] ?? "—");
    }
  }

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Centro de oportunidades</h1>
        <p className="muted">Inteligencia proactiva — detección, priorización y siguiente mejor acción</p>
      </header>

      {error && <p className="error">{error}</p>}

      {summary && (
        <div className="panel metrics-grid">
          <div className="metric-card">
            <span className="metric-label">Detectadas</span>
            <strong>{summary.oportunidades_detectadas}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Pertinentes</span>
            <strong>{summary.pertinentes}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Activadas</span>
            <strong>{summary.activadas}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Materializadas</span>
            <strong>{summary.materializadas}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Valor potencial</span>
            <strong>{formatMoney(summary.valor_potencial_total)}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Valor materializado</span>
            <strong>{formatMoney(summary.valor_materializado_total)}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Pendientes aprobación</span>
            <strong>{summary.pendientes_aprobacion}</strong>
          </div>
        </div>
      )}

      <div className="panel">
        <div className="toolbar" style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", marginBottom: "1rem" }}>
          <input
            type="search"
            placeholder="Buscar oportunidad…"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            title="Buscar por título"
          />
          <select value={filtroEstado} onChange={(e) => setFiltroEstado(e.target.value)} title="Filtrar por estado">
            <option value="">Todos los estados</option>
            <option value="DETECTADA">Detectada</option>
            <option value="EN_EVALUACION">En evaluación</option>
            <option value="PRIORIZADA">Priorizada</option>
            <option value="PENDIENTE_APROBACION">Pendiente aprobación</option>
            <option value="EN_EJECUCION">En ejecución</option>
            <option value="EN_SEGUIMIENTO">En seguimiento</option>
            <option value="MATERIALIZADA">Materializada</option>
            <option value="DATOS_INSUFICIENTES">Datos insuficientes</option>
          </select>
          <select value={filtroDominio} onChange={(e) => setFiltroDominio(e.target.value)} title="Filtrar por dominio">
            <option value="">Todos los dominios</option>
            <option value="administrativo">Administrativo</option>
            <option value="comercial">Comercial</option>
            <option value="financiero">Financiero</option>
            <option value="cumplimiento">Cumplimiento</option>
            <option value="salud">Salud</option>
          </select>
          <details>
            <summary title="Mostrar u ocultar columnas">Columnas</summary>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginTop: "0.5rem" }}>
              {COLUMNAS.map((c) => (
                <label key={c.key} style={{ display: "flex", gap: "0.25rem", alignItems: "center" }}>
                  <input type="checkbox" checked={visibleCols.has(c.key)} onChange={() => toggleCol(c.key)} />
                  {c.label}
                </label>
              ))}
            </div>
          </details>
        </div>

        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                {COLUMNAS.filter((c) => visibleCols.has(c.key)).map((c) => (
                  <th key={c.key}>{c.label}</th>
                ))}
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 && (
                <tr>
                  <td colSpan={visibleCols.size + 1} className="muted">No hay oportunidades que coincidan</td>
                </tr>
              )}
              {items.map((item) => (
                <tr key={item.id}>
                  {COLUMNAS.filter((c) => visibleCols.has(c.key)).map((c) => (
                    <td key={c.key}>{cellValue(item, c.key)}</td>
                  ))}
                  <td>
                    <Link to={`/oportunidades/${item.id}`} title="Ver detalle">Detalle</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
