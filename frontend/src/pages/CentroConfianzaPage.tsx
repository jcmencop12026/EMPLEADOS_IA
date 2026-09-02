import { useCallback, useEffect, useMemo, useState } from "react";
import type { ConfianzaCentro, GobiernoSolicitud } from "../api";
import {
  fetchCentroConfianza,
  fetchGobiernoSolicitudes,
  fetchGobiernoEventos,
} from "../api";
import { EiaaxTable, type EiaaxColumn } from "../components/EiaaxTable";

function formatEventDetail(value: unknown): string {
  if (value == null) return "—";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (typeof value === "object") {
    const o = value as Record<string, unknown>;
    if (typeof o.mensaje === "string") return o.mensaje;
    if (typeof o.descripcion === "string") return o.descripcion;
    if (typeof o.resumen === "string") return o.resumen;
    try {
      return JSON.stringify(value);
    } catch {
      return "—";
    }
  }
  return String(value);
}

type ControlRow = ConfianzaCentro["controles"][number];

export function CentroConfianzaPage() {
  const [centro, setCentro] = useState<ConfianzaCentro | null>(null);
  const [solicitudes, setSolicitudes] = useState<GobiernoSolicitud[]>([]);
  const [eventos, setEventos] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setError(null);
    return Promise.all([
      fetchCentroConfianza().then(setCentro).catch((e) => setError(String(e))),
      fetchGobiernoSolicitudes().then(setSolicitudes).catch(() => undefined),
      fetchGobiernoEventos().then(setEventos).catch(() => undefined),
    ]);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const estadoClass = (estado: string) => {
    if (estado === "ACTIVO" || estado === "CONFIGURADO") return "trust-status-ok";
    return "trust-status-neutral";
  };

  const controlesColumns = useMemo<EiaaxColumn<ControlRow>[]>(() => [
    { key: "nombre", label: "Control", sortable: true, getValue: (c) => c.nombre },
    {
      key: "estado",
      label: "Estado",
      sortable: true,
      getValue: (c) => c.estado,
      render: (c) => <span className={`trust-status ${estadoClass(c.estado)}`}>{c.estado}</span>,
    },
    { key: "evidencia", label: "Evidencia", getValue: (c) => c.evidencia ?? "" },
  ], []);

  const solicitudesColumns = useMemo<EiaaxColumn<GobiernoSolicitud>[]>(() => [
    { key: "tipo_accion", label: "Tipo", sortable: true, getValue: (s) => s.tipo_accion },
    { key: "estado", label: "Estado", sortable: true, getValue: (s) => s.estado },
    { key: "descripcion", label: "Detalle", getValue: (s) => s.descripcion ?? "" },
  ], []);

  const eventosColumns = useMemo<EiaaxColumn<Record<string, unknown>>[]>(() => [
    { key: "tipo", label: "Evento", sortable: true, getValue: (ev) => String(ev.tipo ?? ev.action ?? "") },
    { key: "detalle", label: "Detalle", getValue: (ev) => formatEventDetail(ev.detalle ?? ev.detail) },
  ], []);

  return (
    <div className="ops-page trust-center-page">
      <header className="page-header compact">
        <h1>Centro de Confianza</h1>
        <p className="muted">Seguridad, gobierno, auditoría y evidencia operacional</p>
      </header>

      {error && <div className="alert alert-error">{error}</div>}

      {centro && (
        <div className="trust-layout">
          <section className="panel compact-panel trust-summary">
            <h2 className="section-title">Resumen</h2>
            <div className="cc-kpi-strip">
              <div className="cc-kpi-item">
                <span className="cc-kpi-label">Controles activos</span>
                <strong className="cc-kpi-value">{centro.resumen.controles_activos}</strong>
              </div>
              <div className="cc-kpi-item">
                <span className="cc-kpi-label">Eventos de gobierno</span>
                <strong className="cc-kpi-value">{centro.resumen.eventos_gobierno}</strong>
              </div>
            </div>
            <p className="muted small">Generado: {new Date(centro.generado_en).toLocaleString("es-CO")}</p>
          </section>

          <section className="panel compact-panel">
            <h2 className="section-title">Controles implementados</h2>
            <EiaaxTable
              columns={controlesColumns}
              data={centro.controles}
              rowKey={(c) => c.id}
              prefsKey="confianza-controles"
              searchPlaceholder="Buscar control…"
              emptyMessage="Sin controles con evidencia registrada aún."
            />
          </section>

          <section className="panel compact-panel">
            <h2 className="section-title">Solicitudes de gobierno</h2>
            <EiaaxTable
              columns={solicitudesColumns}
              data={solicitudes}
              rowKey={(s) => s.id}
              prefsKey="confianza-solicitudes"
              searchPlaceholder="Buscar solicitud…"
              emptyMessage="Sin solicitudes pendientes."
            />
          </section>

          <section className="panel compact-panel">
            <h2 className="section-title">Eventos recientes</h2>
            <EiaaxTable
              columns={eventosColumns}
              data={eventos}
              rowKey={(ev) => String(ev.id ?? `${String(ev.tipo ?? ev.action)}-${String(ev.fecha ?? "")}`)}
              prefsKey="confianza-eventos"
              searchPlaceholder="Buscar evento…"
              emptyMessage="Sin eventos recientes."
            />
          </section>
        </div>
      )}
    </div>
  );
}
