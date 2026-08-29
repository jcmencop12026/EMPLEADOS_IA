import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import type { IntegrationCatalogItem, IntegrationConnectorOverview } from "../api";
import { fetchIntegrationCatalog, fetchIntegrationConnectorsOverview } from "../api";
import { usePermissions } from "../hooks/usePermissions";
import {
  INTEGRATION_STATUS_LABELS,
  INTEGRATION_TYPE_LABELS,
  POLICY_DECISION_LABELS,
  formatTs,
} from "./integrationLabels";

const COLUMNAS = [
  { key: "name", label: "Nombre" },
  { key: "connector_type", label: "Tipo" },
  { key: "status", label: "Estado" },
  { key: "organization_name", label: "Organización" },
  { key: "proveedor_ref", label: "Proveedor" },
  { key: "ultima_ejecucion", label: "Última ejecución" },
  { key: "salud", label: "Salud" },
  { key: "ultimo_error", label: "Último error" },
  { key: "politica_decision", label: "Política" },
  { key: "continuidad_estado", label: "Continuidad" },
] as const;

const COLS_KEY = "integraciones_cols_v1";

function loadVisibleCols(): Set<string> {
  try {
    const raw = localStorage.getItem(COLS_KEY);
    if (raw) return new Set(JSON.parse(raw) as string[]);
  } catch {
    /* ignore */
  }
  return new Set(COLUMNAS.map((c) => c.key));
}

type SortKey = typeof COLUMNAS[number]["key"];
type SortDir = "asc" | "desc";

export function IntegracionesPage() {
  const { has } = usePermissions();
  const [connectors, setConnectors] = useState<IntegrationConnectorOverview[]>([]);
  const [catalog, setCatalog] = useState<IntegrationCatalogItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busqueda, setBusqueda] = useState("");
  const [filtroEstado, setFiltroEstado] = useState("");
  const [filtroTipo, setFiltroTipo] = useState("");
  const [visibleCols, setVisibleCols] = useState<Set<string>>(loadVisibleCols);
  const [sortKey, setSortKey] = useState<SortKey>("name");
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  useEffect(() => {
    localStorage.setItem(COLS_KEY, JSON.stringify([...visibleCols]));
  }, [visibleCols]);

  useEffect(() => {
    Promise.all([fetchIntegrationConnectorsOverview(), fetchIntegrationCatalog()])
      .then(([list, cat]) => {
        setConnectors(list);
        setCatalog(cat);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar integraciones"));
  }, []);

  const filtered = useMemo(() => {
    let rows = connectors.filter((c) => {
      const q = busqueda.trim().toLowerCase();
      const matchQ =
        !q ||
        c.name.toLowerCase().includes(q) ||
        c.code.toLowerCase().includes(q) ||
        (c.proveedor_ref ?? "").toLowerCase().includes(q);
      const matchEstado = !filtroEstado || c.status === filtroEstado;
      const matchTipo = !filtroTipo || c.connector_type === filtroTipo;
      return matchQ && matchEstado && matchTipo;
    });
    rows = [...rows].sort((a, b) => {
      const dir = sortDir === "asc" ? 1 : -1;
      const getVal = (row: IntegrationConnectorOverview): string => {
        switch (sortKey) {
          case "ultima_ejecucion":
            return row.ultima_ejecucion?.started_at ?? "";
          case "salud":
            return row.health.circuit_open ? "DEGRADADO" : row.status;
          case "ultimo_error":
            return row.health.last_error_at ?? "";
          default:
            return String((row as Record<string, unknown>)[sortKey] ?? "");
        }
      };
      return getVal(a).localeCompare(getVal(b), "es") * dir;
    });
    return rows;
  }, [connectors, busqueda, filtroEstado, filtroTipo, sortKey, sortDir]);

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  }

  function toggleCol(key: string) {
    setVisibleCols((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Integraciones</h1>
          <p className="muted">
            Vista operativa del cableado 1330/1350/1360: conectores, gobierno, continuidad y trazabilidad.
          </p>
        </div>
        <div className="toolbar">
          <Link className="btn" to="/integraciones/trazabilidad">Trazabilidad</Link>
          {has("integraciones.create") && (
            <Link className="btn primary" to="/integraciones/nueva">Nueva integración</Link>
          )}
        </div>
      </header>

      {error && <div className="alert alert-error">{error}</div>}

      <section className="card" style={{ marginBottom: "1rem" }}>
        <h2>Catálogo de tipos</h2>
        <div className="chip-row">
          {catalog.map((t) => (
            <span key={t.type} className="chip" title={t.descripcion}>{t.name}</span>
          ))}
        </div>
      </section>

      <section className="card">
        <div className="toolbar" style={{ marginBottom: "1rem", flexWrap: "wrap", gap: "0.5rem" }}>
          <input
            placeholder="Buscar nombre, código o proveedor"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
          />
          <select value={filtroEstado} onChange={(e) => setFiltroEstado(e.target.value)}>
            <option value="">Todos los estados</option>
            {Object.entries(INTEGRATION_STATUS_LABELS).map(([k, v]) => (
              <option key={k} value={k}>{v}</option>
            ))}
          </select>
          <select value={filtroTipo} onChange={(e) => setFiltroTipo(e.target.value)}>
            <option value="">Todos los tipos</option>
            {Object.entries(INTEGRATION_TYPE_LABELS).map(([k, v]) => (
              <option key={k} value={k}>{v}</option>
            ))}
          </select>
          <details>
            <summary className="btn">Columnas</summary>
            <div className="chip-row" style={{ marginTop: "0.5rem" }}>
              {COLUMNAS.map((c) => (
                <label key={c.key} className="chip">
                  <input
                    type="checkbox"
                    checked={visibleCols.has(c.key)}
                    onChange={() => toggleCol(c.key)}
                  />
                  {c.label}
                </label>
              ))}
            </div>
          </details>
        </div>

        {filtered.length === 0 ? (
          <p className="muted">No hay conectores que coincidan con el filtro.</p>
        ) : (
          <div className="table-wrap">
            <table className="data-table compact">
              <thead>
                <tr>
                  {COLUMNAS.filter((c) => visibleCols.has(c.key)).map((c) => (
                    <th key={c.key}>
                      <button type="button" className="linkish" onClick={() => toggleSort(c.key)}>
                        {c.label}{sortKey === c.key ? (sortDir === "asc" ? " ↑" : " ↓") : ""}
                      </button>
                    </th>
                  ))}
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((c) => (
                  <tr key={c.id}>
                    {visibleCols.has("name") && <td><Link to={`/integraciones/${c.id}`}>{c.name}</Link></td>}
                    {visibleCols.has("connector_type") && (
                      <td>{INTEGRATION_TYPE_LABELS[c.connector_type] ?? c.connector_type}</td>
                    )}
                    {visibleCols.has("status") && (
                      <td>
                        <span className={`badge status-${c.status}`}>
                          {INTEGRATION_STATUS_LABELS[c.status] ?? c.status}
                        </span>
                      </td>
                    )}
                    {visibleCols.has("organization_name") && <td>{c.organization_name ?? "—"}</td>}
                    {visibleCols.has("proveedor_ref") && <td className="mono-sm">{c.proveedor_ref ?? "—"}</td>}
                    {visibleCols.has("ultima_ejecucion") && (
                      <td>
                        {c.ultima_ejecucion
                          ? `${formatTs(c.ultima_ejecucion.started_at)} · ${c.ultima_ejecucion.status}`
                          : "—"}
                      </td>
                    )}
                    {visibleCols.has("salud") && (
                      <td>
                        {c.health.circuit_open ? "Cortacircuitos abierto" : INTEGRATION_STATUS_LABELS[c.status] ?? c.status}
                        {c.health.consecutive_failures > 0 ? ` (${c.health.consecutive_failures} fallos)` : ""}
                      </td>
                    )}
                    {visibleCols.has("ultimo_error") && (
                      <td className="truncate" title={c.health.last_error_message ?? ""}>
                        {c.health.last_error_message ?? "—"}
                      </td>
                    )}
                    {visibleCols.has("politica_decision") && (
                      <td>
                        {c.politica_decision
                          ? POLICY_DECISION_LABELS[c.politica_decision] ?? c.politica_decision
                          : "Sin catálogo"}
                      </td>
                    )}
                    {visibleCols.has("continuidad_estado") && <td>{c.continuidad_estado ?? "—"}</td>}
                    <td className="actions-cell">
                      <Link to={`/integraciones/${c.id}`}>Detalle</Link>
                      {c.ultima_ejecucion?.correlation_id && (
                        <>
                          {" · "}
                          <Link to={`/integraciones/trazabilidad?cid=${encodeURIComponent(c.ultima_ejecucion.correlation_id)}`}>
                            Traza
                          </Link>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
