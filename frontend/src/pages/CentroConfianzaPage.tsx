import { useCallback, useEffect, useState } from "react";
import type { ConfianzaCentro, GobiernoSolicitud } from "../api";
import {
  fetchCentroConfianza,
  fetchGobiernoSolicitudes,
  fetchGobiernoEventos,
} from "../api";

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
            {centro.controles.length === 0 ? (
              <p className="muted">Sin controles con evidencia registrada aún.</p>
            ) : (
              <table className="data-table compact-table cc-table-fill">
                <thead>
                  <tr><th>Control</th><th>Estado</th><th>Evidencia</th></tr>
                </thead>
                <tbody>
                  {centro.controles.map((c) => (
                    <tr key={c.id}>
                      <td>{c.nombre}</td>
                      <td><span className={`trust-status ${estadoClass(c.estado)}`}>{c.estado}</span></td>
                      <td>{c.evidencia ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>

          <section className="panel compact-panel">
            <h2 className="section-title">Solicitudes de gobierno</h2>
            {solicitudes.length === 0 ? (
              <p className="muted">Sin solicitudes pendientes.</p>
            ) : (
              <table className="data-table compact-table cc-table-fill">
                <thead>
                  <tr><th>Tipo</th><th>Estado</th><th>Detalle</th></tr>
                </thead>
                <tbody>
                  {solicitudes.slice(0, 8).map((s) => (
                    <tr key={s.id}>
                      <td>{s.tipo_accion}</td>
                      <td>{s.estado}</td>
                      <td>{s.descripcion ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>

          <section className="panel compact-panel">
            <h2 className="section-title">Eventos recientes</h2>
            {eventos.length === 0 ? (
              <p className="muted">Sin eventos recientes.</p>
            ) : (
              <table className="data-table compact-table cc-table-fill">
                <thead>
                  <tr><th>Evento</th><th>Detalle</th></tr>
                </thead>
                <tbody>
                  {eventos.slice(0, 8).map((ev, idx) => (
                    <tr key={String(ev.id ?? idx)}>
                      <td>{String(ev.tipo ?? ev.action ?? "—")}</td>
                      <td>{String(ev.detalle ?? ev.detail ?? "—")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
