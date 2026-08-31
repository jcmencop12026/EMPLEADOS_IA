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

  const estadoColor = (estado: string) => {
    if (estado === "ACTIVO" || estado === "CONFIGURADO") return "#0a7";
    return "#666";
  };

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Centro de Confianza</h1>
          <p className="muted">
            Controles operacionales con evidencia real — sin certificaciones ficticias.
          </p>
        </div>
      </header>

      {error && <div className="alert alert-error">{error}</div>}

      {centro && (
        <>
          <section className="card" style={{ marginBottom: "1rem" }}>
            <h2>Resumen</h2>
            <p>
              <strong>{centro.resumen.controles_activos}</strong> control(es) con evidencia ·{" "}
              <strong>{centro.resumen.eventos_gobierno}</strong> evento(s) de gobierno
            </p>
            <p className="muted" style={{ fontSize: "0.85rem" }}>
              Generado: {new Date(centro.generado_en).toLocaleString()}
            </p>
          </section>

          <section className="card" style={{ marginBottom: "1rem" }}>
            <h2>Controles implementados</h2>
            {centro.controles.length === 0 ? (
              <p className="muted">Sin controles con evidencia registrada aún.</p>
            ) : (
              <div style={{ display: "grid", gap: "0.75rem" }}>
                {centro.controles.map((c) => (
                  <div
                    key={c.id}
                    style={{
                      border: "1px solid #e0e0e0",
                      borderRadius: 8,
                      padding: "0.75rem 1rem",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <strong>{c.nombre}</strong>
                      <span style={{ color: estadoColor(c.estado), fontWeight: 600, fontSize: "0.85rem" }}>
                        {c.estado}
                      </span>
                    </div>
                    {c.evidencia && <p style={{ margin: "0.35rem 0 0", fontSize: "0.9rem" }}>{c.evidencia}</p>}
                  </div>
                ))}
              </div>
            )}
          </section>
        </>
      )}

      <section className="card" style={{ marginBottom: "1rem" }}>
        <h2>Solicitudes recientes</h2>
        {solicitudes.length === 0 ? (
          <p className="muted">Sin solicitudes de acción registradas.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Tipo</th>
                <th>Recurso</th>
                <th>Estado</th>
                <th>Descripción</th>
              </tr>
            </thead>
            <tbody>
              {solicitudes.slice(0, 10).map((s) => (
                <tr key={s.id}>
                  <td>{s.tipo_accion}</td>
                  <td>{s.recurso_tipo}</td>
                  <td>{s.estado}</td>
                  <td>{s.descripcion}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="card">
        <h2>Eventos de trazabilidad</h2>
        {eventos.length === 0 ? (
          <p className="muted">Sin eventos de gobierno operacional.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Acción</th>
                <th>Actor</th>
                <th>Recurso</th>
                <th>Resultado</th>
              </tr>
            </thead>
            <tbody>
              {eventos.slice(0, 10).map((e) => (
                <tr key={String(e.id)}>
                  <td>{String(e.accion)}</td>
                  <td>{String(e.actor_tipo)}</td>
                  <td>{String(e.recurso_tipo || "—")}</td>
                  <td>{String(e.resultado || e.decision || "—")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
