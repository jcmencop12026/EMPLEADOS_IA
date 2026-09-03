import { useCallback, useEffect, useState } from "react";
import type { ConfianzaEmpresarial, GobiernoSolicitud } from "../api";
import {
  fetchCentroConfianzaEmpresarial,
  fetchGobiernoSolicitudes,
  fetchGobiernoEventos,
} from "../api";

const ESTADO_COLOR: Record<string, string> = {
  IMPLEMENTADO: "#0a7",
  CONFIGURADO: "#06c",
  PENDIENTE: "#c80",
  NO_DISPONIBLE: "#999",
};

export function CentroConfianzaPage() {
  const [centro, setCentro] = useState<ConfianzaEmpresarial | null>(null);
  const [solicitudes, setSolicitudes] = useState<GobiernoSolicitud[]>([]);
  const [eventos, setEventos] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setError(null);
    return Promise.all([
      fetchCentroConfianzaEmpresarial().then(setCentro).catch((e) => setError(String(e))),
      fetchGobiernoSolicitudes().then(setSolicitudes).catch(() => undefined),
      fetchGobiernoEventos().then(setEventos).catch(() => undefined),
    ]);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Centro de Confianza</h1>
          <p className="muted">
            Controles verificables agrupados por dominio — sin certificaciones ficticias.
          </p>
        </div>
      </header>

      {error && <div className="alert alert-error">{error}</div>}

      {centro && (
        <>
          <section className="card" style={{ marginBottom: "1rem" }}>
            <h2>Resumen</h2>
            <p>
              <strong>{centro.resumen.implementados}</strong> implementado(s) ·{" "}
              <strong>{centro.resumen.configurados}</strong> configurado(s) ·{" "}
              <strong>{centro.resumen.pendientes}</strong> pendiente(s)
            </p>
            <p className="muted" style={{ fontSize: "0.85rem" }}>
              Generado: {new Date(centro.generado_en).toLocaleString()}
            </p>
          </section>

          {centro.grupos.map((grupo) => (
            <section key={grupo.id} className="card" style={{ marginBottom: "1rem" }}>
              <h2>{grupo.etiqueta}</h2>
              <div style={{ display: "grid", gap: "0.75rem" }}>
                {grupo.controles.map((c) => (
                  <div
                    key={c.id}
                    style={{ border: "1px solid #e0e0e0", borderRadius: 8, padding: "0.75rem 1rem" }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <strong>{c.nombre}</strong>
                      <span
                        style={{
                          color: ESTADO_COLOR[c.estado] || "#666",
                          fontWeight: 600,
                          fontSize: "0.85rem",
                        }}
                      >
                        {c.estado_etiqueta}
                      </span>
                    </div>
                    {c.evidencia && (
                      <p style={{ margin: "0.35rem 0 0", fontSize: "0.9rem" }}>{c.evidencia}</p>
                    )}
                  </div>
                ))}
              </div>
            </section>
          ))}
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
