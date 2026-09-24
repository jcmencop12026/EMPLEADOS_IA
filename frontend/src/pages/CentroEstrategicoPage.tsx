import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchCentroEstrategicoCockpit, type CentroEstrategicoCockpit } from "../api";
import { useOrganizationContext } from "../hooks/useOrganizationContext";
import { usePermissions } from "../hooks/usePermissions";

const LECTURAS = [
  { id: "resumen", label: "Resumen" },
  { id: "gerencia", label: "Gerencia" },
  { id: "operacion", label: "Operación" },
  { id: "sistemas", label: "Sistemas" },
  { id: "financiero", label: "Financiero" },
] as const;

type LecturaId = (typeof LECTURAS)[number]["id"];

function fmt(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "number") return v.toLocaleString("es-CO");
  return String(v);
}

function GraficoComparacion({ chart }: { chart: CentroEstrategicoCockpit["graficos"][0] }) {
  const max = Math.max(
    ...chart.series.map((s) => (typeof s.valor === "number" ? s.valor : 0)),
    1,
  );
  return (
    <div className="cc-chart-block">
      <h4>{chart.titulo}</h4>
      <div className="cc-chart-bars">
        {chart.series.map((s) => (
          <div key={s.etiqueta} className={`cc-bar cc-bar-${s.naturaleza.toLowerCase()}`}>
            <span className="cc-bar-label">{s.etiqueta}</span>
            <div className="cc-bar-track">
              <div
                className="cc-bar-fill"
                style={{ width: `${Math.min(100, ((Number(s.valor) || 0) / max) * 100)}%` }}
                title={String(s.valor ?? "Sin dato")}
              />
            </div>
            <span className="cc-bar-value">{fmt(s.valor)}</span>
          </div>
        ))}
      </div>
      {chart.nota && <p className="muted small">{chart.nota}</p>}
    </div>
  );
}

export function CentroEstrategicoPage() {
  const { has } = usePermissions();
  const { organizationQueryParam } = useOrganizationContext();
  const [data, setData] = useState<CentroEstrategicoCockpit | null>(null);
  const [lectura, setLectura] = useState<LecturaId>("resumen");
  const [modoComite, setModoComite] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchCentroEstrategicoCockpit(lectura, modoComite, organizationQueryParam)
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Error"))
      .finally(() => setLoading(false));
  }, [lectura, modoComite, organizationQueryParam]);

  useEffect(() => {
    load();
  }, [load]);

  if (!has("strategic_control.view")) {
    return <p className="error">No tiene permiso para el Centro Estratégico.</p>;
  }

  const c = data?.contenido as Record<string, unknown> | undefined;

  return (
    <div className="ops-page centro-estrategico-page">
      <header className="page-header compact">
        <h1>Centro de Control estratégico</h1>
        <p className="muted">
          Cockpit de empresa/prospecto — mismo dossier, lecturas complementarias.
          {data?.generated_at && <> · Actualizado: {new Date(data.generated_at).toLocaleString("es-CO")}</>}
        </p>
        <div className="toolbar compact-toolbar">
          <label className="inline-check">
            <input type="checkbox" checked={modoComite} onChange={(e) => setModoComite(e.target.checked)} />
            Modo comité
          </label>
          <button type="button" onClick={load} disabled={loading}>Actualizar</button>
          <Link to="/centro-control" className="btn-link">→ Centro operacional (MB-08)</Link>
        </div>
      </header>

      <nav className="tab-bar compact-tabs" aria-label="Lecturas estratégicas">
        {LECTURAS.map((l) => (
          <button
            key={l.id}
            type="button"
            className={`tab-btn ${lectura === l.id ? "active" : ""}`}
            onClick={() => setLectura(l.id)}
          >
            {l.label}
          </button>
        ))}
      </nav>

      {loading && <p className="muted">Cargando cockpit…</p>}
      {error && <p className="error">{error}</p>}

      {data && (
        <>
          <section className="panel compact-panel">
            <p className="muted">{data.separacion_mb08}</p>
            {modoComite && <p className="muted">{data.nota_comite}</p>}
          </section>

          {lectura === "resumen" && c && (
            <section className="panel compact-panel">
              <h2 className="section-title">Resumen del dossier</h2>
              <dl className="detail-grid">
                <dt>Etapa</dt><dd>{fmt(c.etapa)}</dd>
                <dt>Entidad</dt><dd>{fmt(c.entidad)}</dd>
                <dt>Completitud</dt><dd>{fmt(c.completitud)}%</dd>
                <dt>Confianza</dt><dd>{fmt(c.confianza)}</dd>
                <dt>Alternativas</dt><dd>{fmt(c.alternativas)}</dd>
                <dt>Iniciativas</dt><dd>{fmt(c.iniciativas)}</dd>
              </dl>
              <p><Link to={data.enlaces.arquitecto}>Arquitecto de Transformación</Link></p>
            </section>
          )}

          {lectura === "gerencia" && c && (
            <section className="panel compact-panel">
              <h2 className="section-title">Gerencia</h2>
              <div className="metrics-grid compact">
                <div className="metric-card"><span className="metric-label">Valor verificado</span><strong>{fmt((c.valor as Record<string,unknown>)?.verificado)}</strong></div>
                <div className="metric-card"><span className="metric-label">Valor estimado</span><strong>{fmt((c.valor as Record<string,unknown>)?.estimado)}</strong></div>
                <div className="metric-card potential-excluded"><span className="metric-label">Potencial</span><strong>{fmt((c.valor as Record<string,unknown>)?.potencial)}</strong></div>
              </div>
              {(c.riesgos as Array<Record<string,string>>)?.length > 0 && (
                <table className="data-table compact-table">
                  <thead><tr><th>Riesgo</th><th>Severidad</th></tr></thead>
                  <tbody>
                    {(c.riesgos as Array<Record<string,string>>).map((r, i) => (
                      <tr key={i}><td>{r.titulo}</td><td>{r.severidad}</td></tr>
                    ))}
                  </tbody>
                </table>
              )}
            </section>
          )}

          {lectura === "operacion" && c && (
            <section className="panel compact-panel">
              <h2 className="section-title">Operación estratégica</h2>
              <p className="muted">Procesos y capacidad — no duplica ejecuciones MB-08.</p>
              {(c.enlace_operacional_mb08 as Record<string,unknown>)?.disponible && (
                <p><Link to="/centro-control">Ver ejecuciones operativas (MB-08)</Link></p>
              )}
            </section>
          )}

          {lectura === "sistemas" && c && (
            <section className="panel compact-panel">
              <h2 className="section-title">Sistemas</h2>
              <dl className="detail-grid">
                <dt>Conectores</dt><dd>{fmt((c.integraciones as Record<string,unknown>)?.conectores)}</dd>
                <dt>Activos</dt><dd>{fmt((c.integraciones as Record<string,unknown>)?.activos)}</dd>
              </dl>
              <p><Link to="/integraciones">Integraciones</Link></p>
            </section>
          )}

          {lectura === "financiero" && c && (
            <section className="panel compact-panel">
              <h2 className="section-title">Financiero</h2>
              <p className="muted">{data.semantica_valor?.nota}</p>
              {(c.economia_privada as Record<string,unknown>)?.restringido && (
                <p className="muted">Economía privada restringida — requiere permiso interno.</p>
              )}
              <p><Link to="/comercial">Comercial</Link> · <Link to="/tco">TCO</Link></p>
            </section>
          )}

          {data.graficos.length > 0 && (
            <section className="panel compact-panel">
              <h2 className="section-title">Comparación ANTES / PROYECTADO / REAL</h2>
              {data.graficos.map((g, i) => (
                <GraficoComparacion key={i} chart={g} />
              ))}
            </section>
          )}

          {data.trazabilidad?.cadena_ejecutiva && data.trazabilidad.cadena_ejecutiva.length > 0 && (
            <section className="panel compact-panel">
              <h2 className="section-title">Trazabilidad cadena de valor</h2>
              <table className="data-table compact-table">
                <thead><tr><th>Oportunidad</th><th>Etapas</th></tr></thead>
                <tbody>
                  {data.trazabilidad.cadena_ejecutiva.map((cad) => (
                    <tr key={cad.oportunidad_id as string}>
                      <td>{String(cad.titulo)}</td>
                      <td>
                        {(cad.etapas as Array<{ etapa: string; enlace: string }>).map((e) => (
                          <Link key={e.etapa} to={e.enlace} className="cc-chain-link">{e.etapa} </Link>
                        ))}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}

          {data.vista_entidad && (
            <section className="panel compact-panel">
              <h2 className="section-title">Vista entidad (publicable)</h2>
              <p className="muted">{data.publicacion?.nota}</p>
              <p>Hallazgos visibles: {(data.vista_entidad.hallazgos as unknown[])?.length ?? 0}</p>
            </section>
          )}
        </>
      )}
    </div>
  );
}
