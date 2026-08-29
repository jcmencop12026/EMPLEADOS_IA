import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  ApiError,
  approveOpportunity,
  decideApproval,
  fetchTrabajoItems,
  fetchTrabajoResumen,
  transitionNotification,
  type TrabajoItem,
  type TrabajoResumen,
} from "../api";
import { EmptyState, ErrorState, LoadingState } from "../components/AsyncState";
import { usePermissions } from "../hooks/usePermissions";

const COLUMNAS = [
  { key: "tipo", label: "Tipo" },
  { key: "asunto", label: "Asunto" },
  { key: "modulo", label: "Módulo" },
  { key: "prioridad", label: "Prioridad" },
  { key: "estado_presentacion", label: "Estado" },
  { key: "responsable_nombre", label: "Responsable" },
  { key: "created_at", label: "Creación" },
  { key: "fecha_limite", label: "Límite" },
  { key: "correlation_id", label: "Correlation" },
] as const;

const COLS_KEY = "trabajo_cols_v1";

const TIPO_LABELS: Record<string, string> = {
  aprobacion: "Aprobación",
  oportunidad_aprobacion: "Oportunidad",
  notificacion: "Notificación",
  tarea_vencida: "Tarea vencida",
  ejecucion_fallida: "Ejecución fallida",
  automatizacion_fallida: "Automatización",
  alerta_continuidad: "Alerta continuidad",
  integracion_degradada: "Integración",
  presupuesto_ia: "Presupuesto IA",
  soporte_caso: "Caso soporte",
  soporte_asignacion: "Asignación soporte",
  soporte_sla_riesgo: "SLA en riesgo",
  soporte_sla_vencido: "SLA vencido",
};

const MODULO_LABELS: Record<string, string> = {
  soporte: "Mesa de Ayuda",
};

const ESTADO_LABELS: Record<string, string> = {
  PENDIENTE: "Pendiente",
  EN_CURSO: "En curso",
  REQUIERE_APROBACION: "Requiere aprobación",
  VENCIDA: "Vencida",
  COMPLETADA: "Completada",
  FALLIDA: "Fallida",
};

function loadVisibleCols(): Set<string> {
  try {
    const raw = localStorage.getItem(COLS_KEY);
    if (raw) return new Set(JSON.parse(raw) as string[]);
  } catch {
    /* ignore */
  }
  return new Set(COLUMNAS.map((c) => c.key));
}

function formatTs(value?: string | null) {
  if (!value) return "—";
  return new Date(value).toLocaleString("es");
}

export function TrabajoPage() {
  const { has } = usePermissions();
  const [items, setItems] = useState<TrabajoItem[]>([]);
  const [resumen, setResumen] = useState<TrabajoResumen | null>(null);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [acting, setActing] = useState<string | null>(null);
  const [selected, setSelected] = useState<TrabajoItem | null>(null);
  const [busqueda, setBusqueda] = useState("");
  const [filtroEstado, setFiltroEstado] = useState("");
  const [filtroPrioridad, setFiltroPrioridad] = useState("");
  const [filtroTipo, setFiltroTipo] = useState("");
  const [filtroModulo, setFiltroModulo] = useState("");
  const [filtroVencimiento, setFiltroVencimiento] = useState("");
  const [soloAccion, setSoloAccion] = useState(false);
  const [sortKey, setSortKey] = useState("prioridad");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [visibleCols, setVisibleCols] = useState<Set<string>>(loadVisibleCols);

  useEffect(() => {
    localStorage.setItem(COLS_KEY, JSON.stringify([...visibleCols]));
  }, [visibleCols]);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    const params: Record<string, string | boolean | undefined> = {
      q: busqueda.trim() || undefined,
      estado: filtroEstado || undefined,
      prioridad: filtroPrioridad || undefined,
      tipo: filtroTipo || undefined,
      modulo: filtroModulo || undefined,
      vencimiento: filtroVencimiento || undefined,
      requires_action: soloAccion ? true : undefined,
      sort: sortKey,
      sort_dir: sortDir,
    };
    return Promise.all([fetchTrabajoItems(params), fetchTrabajoResumen()])
      .then(([data, sum]) => {
        setItems(data.items);
        setTotal(data.total);
        setResumen(sum);
        setSelected((prev) => {
          if (!prev) return data.items[0] ?? null;
          return data.items.find((i) => i.id === prev.id) ?? data.items[0] ?? null;
        });
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Error al cargar la bandeja."))
      .finally(() => setLoading(false));
  }, [busqueda, filtroEstado, filtroPrioridad, filtroTipo, filtroModulo, filtroVencimiento, soloAccion, sortKey, sortDir]);

  useEffect(() => {
    void load();
  }, [load]);

  const modulos = useMemo(() => [...new Set(items.map((i) => i.modulo))].sort(), [items]);
  const tipos = useMemo(() => [...new Set(items.map((i) => i.tipo))].sort(), [items]);

  async function runAction(item: TrabajoItem, accion: TrabajoItem["acciones"][number]) {
    if (accion.permiso && !has(accion.permiso)) return;
    setActing(`${item.id}:${accion.codigo}`);
    setError(null);
    try {
      const payload = accion.payload ?? {};
      if (accion.codigo === "aprobar" && payload.approval_id) {
        await decideApproval(String(payload.approval_id), "approve");
      } else if (accion.codigo === "rechazar" && payload.approval_id) {
        await decideApproval(String(payload.approval_id), "reject");
      } else if (accion.codigo === "aprobar" && payload.opportunity_id) {
        await approveOpportunity(String(payload.opportunity_id), true);
      } else if (accion.codigo === "rechazar" && payload.opportunity_id) {
        await approveOpportunity(String(payload.opportunity_id), false);
      } else if (accion.codigo === "leer" && payload.notification_id) {
        await transitionNotification(String(payload.notification_id), "read");
        window.dispatchEvent(new Event("notifications-changed"));
      } else if (accion.codigo === "atender" && payload.notification_id) {
        await transitionNotification(String(payload.notification_id), "acknowledge");
        window.dispatchEvent(new Event("notifications-changed"));
      }
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo completar la acción.");
    } finally {
      setActing(null);
    }
  }

  function toggleSort(key: string) {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  if (loading && items.length === 0) {
    return <LoadingState message="Cargando bandeja de trabajo…" />;
  }

  return (
    <div className="ops-page trabajo-page">
      <header className="page-header">
        <div>
          <h1>Mi trabajo</h1>
          <p className="muted">Tareas, alertas, aprobaciones y notificaciones que requieren su atención</p>
        </div>
        {resumen && (
          <div className="trabajo-counters" aria-label="Resumen bandeja">
            <span className="badge">{resumen.pendientes} pendientes</span>
            <span className="badge warn">{resumen.vencidas} vencidas</span>
            <span className="badge info">{resumen.requieren_aprobacion} aprobación</span>
          </div>
        )}
      </header>

      <div className="trabajo-filters panel">
        <input
          type="search"
          placeholder="Buscar asunto, detalle o módulo"
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
          aria-label="Buscar"
        />
        <select value={filtroEstado} onChange={(e) => setFiltroEstado(e.target.value)} aria-label="Estado">
          <option value="">Estado</option>
          {Object.entries(ESTADO_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
        <select value={filtroPrioridad} onChange={(e) => setFiltroPrioridad(e.target.value)} aria-label="Prioridad">
          <option value="">Prioridad</option>
          {["CRITICA", "ALTA", "MEDIA", "BAJA"].map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
        <select value={filtroTipo} onChange={(e) => setFiltroTipo(e.target.value)} aria-label="Tipo">
          <option value="">Tipo</option>
          {tipos.map((t) => (
            <option key={t} value={t}>{TIPO_LABELS[t] ?? t}</option>
          ))}
        </select>
        <select value={filtroModulo} onChange={(e) => setFiltroModulo(e.target.value)} aria-label="Módulo">
          <option value="">Módulo</option>
          {modulos.map((m) => (
            <option key={m} value={m}>{MODULO_LABELS[m] ?? m}</option>
          ))}
        </select>
        <select value={filtroVencimiento} onChange={(e) => setFiltroVencimiento(e.target.value)} aria-label="Vencimiento">
          <option value="">Vencimiento</option>
          <option value="vencida">Vencidas</option>
          <option value="proxima">Próximas 3 días</option>
          <option value="sin_limite">Sin límite</option>
        </select>
        <label className="checkbox-inline">
          <input type="checkbox" checked={soloAccion} onChange={(e) => setSoloAccion(e.target.checked)} />
          Solo requiere acción
        </label>
        <details className="cols-picker">
          <summary>Columnas</summary>
          {COLUMNAS.map((col) => (
            <label key={col.key}>
              <input
                type="checkbox"
                checked={visibleCols.has(col.key)}
                onChange={() => {
                  setVisibleCols((prev) => {
                    const next = new Set(prev);
                    if (next.has(col.key)) next.delete(col.key);
                    else next.add(col.key);
                    return next;
                  });
                }}
              />
              {col.label}
            </label>
          ))}
        </details>
      </div>

      {error && <p className="error" role="alert">{error}</p>}

      {items.length === 0 ? (
        <EmptyState title="Sin elementos" message="No hay ítems en la bandeja con los filtros actuales." />
      ) : (
        <div className="trabajo-layout">
          <div className="panel table-wrap trabajo-grid">
            <p className="muted small">{total} elemento(s)</p>
            <table className="data-table compact">
              <thead>
                <tr>
                  {COLUMNAS.filter((c) => visibleCols.has(c.key)).map((col) => (
                    <th key={col.key}>
                      <button type="button" className="sort-btn" onClick={() => toggleSort(col.key === "estado_presentacion" ? "prioridad" : col.key)}>
                        {col.label}
                      </button>
                    </th>
                  ))}
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {items.map((row) => (
                  <tr
                    key={row.id}
                    className={selected?.id === row.id ? "row-selected" : undefined}
                    onClick={() => setSelected(row)}
                  >
                    {COLUMNAS.filter((c) => visibleCols.has(c.key)).map((col) => {
                      if (col.key === "tipo") {
                        return <td key={col.key}>{TIPO_LABELS[row.tipo] ?? row.tipo}</td>;
                      }
                      if (col.key === "modulo") {
                        return <td key={col.key}>{MODULO_LABELS[row.modulo] ?? row.modulo}</td>;
                      }
                      if (col.key === "estado_presentacion") {
                        return <td key={col.key}>{ESTADO_LABELS[row.estado_presentacion] ?? row.estado_presentacion}</td>;
                      }
                      if (col.key === "created_at" || col.key === "fecha_limite") {
                        return <td key={col.key} className="mono">{formatTs(row[col.key])}</td>;
                      }
                      if (col.key === "correlation_id") {
                        return (
                          <td key={col.key} className="mono cell-truncate" title={row.correlation_id ?? ""}>
                            {row.correlation_id ? row.correlation_id.slice(0, 8) : "—"}
                          </td>
                        );
                      }
                      const val = row[col.key as keyof TrabajoItem];
                      return (
                        <td key={col.key} className={col.key === "asunto" ? "cell-truncate" : undefined} title={String(val ?? "")}>
                          {String(val ?? "—")}
                        </td>
                      );
                    })}
                    <td className="notification-actions">
                      {row.acciones.slice(0, 3).map((acc) => {
                        const disabled = Boolean(acc.permiso && !has(acc.permiso)) || acting === `${row.id}:${acc.codigo}`;
                        if (acc.href) {
                          return (
                            <Link key={acc.codigo} to={acc.href} className="btn icon-btn" title={acc.etiqueta} onClick={(e) => e.stopPropagation()}>
                              ↗
                            </Link>
                          );
                        }
                        return (
                          <button
                            key={acc.codigo}
                            type="button"
                            className="btn icon-btn"
                            title={acc.etiqueta}
                            disabled={disabled}
                            onClick={(e) => {
                              e.stopPropagation();
                              void runAction(row, acc);
                            }}
                          >
                            {acc.codigo === "aprobar" ? "✓" : acc.codigo === "rechazar" ? "×" : "•"}
                          </button>
                        );
                      })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {selected && (
            <aside className="panel trabajo-detail">
              <h2>Detalle</h2>
              <dl className="detail-list">
                <dt>Tipo</dt>
                <dd>{TIPO_LABELS[selected.tipo] ?? selected.tipo}</dd>
                <dt>Asunto</dt>
                <dd>{selected.asunto}</dd>
                <dt>Módulo</dt>
                <dd>{MODULO_LABELS[selected.modulo] ?? selected.modulo}</dd>
                <dt>Estado dominio</dt>
                <dd>{selected.estado_dominio}</dd>
                <dt>Estado</dt>
                <dd>{ESTADO_LABELS[selected.estado_presentacion] ?? selected.estado_presentacion}</dd>
                <dt>Prioridad</dt>
                <dd>{selected.prioridad}</dd>
                <dt>Responsable</dt>
                <dd>{selected.responsable_nombre ?? "—"}</dd>
                <dt>Creación</dt>
                <dd className="mono">{formatTs(selected.created_at)}</dd>
                <dt>Límite</dt>
                <dd className="mono">{formatTs(selected.fecha_limite)}</dd>
                {selected.antiguedad_horas != null && (
                  <>
                    <dt>Antigüedad</dt>
                    <dd>{selected.antiguedad_horas} h</dd>
                  </>
                )}
                {selected.correlation_id && (
                  <>
                    <dt>Correlation ID</dt>
                    <dd className="mono">{selected.correlation_id}</dd>
                  </>
                )}
                {selected.semantic_kind && (
                  <>
                    <dt>Semántica</dt>
                    <dd>{selected.semantic_kind}</dd>
                  </>
                )}
                {selected.detalle && (
                  <>
                    <dt>Detalle</dt>
                    <dd>{selected.detalle}</dd>
                  </>
                )}
              </dl>
              <div className="trabajo-detail-actions">
                <Link to={selected.enlace} className="btn">Abrir módulo</Link>
                {selected.trazabilidad_enlace && (
                  <Link to={selected.trazabilidad_enlace} className="btn">Trazabilidad</Link>
                )}
              </div>
              <div className="notification-actions">
                {selected.acciones.map((acc) => {
                  const disabled = Boolean(acc.permiso && !has(acc.permiso)) || acting === `${selected.id}:${acc.codigo}`;
                  if (acc.href) {
                    return (
                      <Link key={acc.codigo} to={acc.href} className="btn" title={acc.etiqueta}>
                        {acc.etiqueta}
                      </Link>
                    );
                  }
                  return (
                    <button
                      key={acc.codigo}
                      type="button"
                      className="btn"
                      disabled={disabled}
                      title={acc.etiqueta}
                      onClick={() => void runAction(selected, acc)}
                    >
                      {acc.etiqueta}
                    </button>
                  );
                })}
              </div>
            </aside>
          )}
        </div>
      )}
    </div>
  );
}
