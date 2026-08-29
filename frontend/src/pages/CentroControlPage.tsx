import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { CentroControlResumen } from "../api";
import { fetchCentroControlResumen } from "../api";
import { usePermissions } from "../hooks/usePermissions";

function ValorIndicador({ valor, disponible, estado }: { valor: unknown; disponible: boolean; estado?: string | null }) {
  if (!disponible) return <span className="muted">{estado ?? "Sin información disponible"}</span>;
  if (valor === null || valor === undefined) return <span className="muted">Sin información disponible</span>;
  return <strong>{String(valor)}</strong>;
}

export function CentroControlPage() {
  const { has } = usePermissions();
  const [data, setData] = useState<CentroControlResumen | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [periodo, setPeriodo] = useState("mtd");

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchCentroControlResumen(periodo)
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar"))
      .finally(() => setLoading(false));
  }, [periodo]);

  useEffect(() => {
    load();
  }, [load]);

  if (!has("control_center.view")) {
    return (
      <div className="ops-page">
        <p className="error">No tiene permiso para ver el Centro de Control.</p>
      </div>
    );
  }

  return (
    <div className="ops-page centro-control-page">
      <header className="page-header compact">
        <h1>Centro de Control ejecutivo</h1>
        <p className="muted">Consolidación operativa — qué pasa, qué requiere atención y qué valor se genera</p>
        <div className="toolbar compact-toolbar">
          <select value={periodo} onChange={(e) => setPeriodo(e.target.value)} title="Periodo">
            <option value="mtd">Mes actual</option>
            <option value="7d">Últimos 7 días</option>
            <option value="30d">Últimos 30 días</option>
          </select>
          <button type="button" onClick={load} disabled={loading}>Actualizar</button>
        </div>
      </header>

      {loading && <p className="muted">Cargando centro de control…</p>}
      {error && <p className="error">{error}</p>}

      {data && (
        <>
          <section className="panel compact-panel">
            <h2 className="section-title">Resumen ejecutivo</h2>
            <div className="metrics-grid">
              {data.resumen_ejecutivo.indicadores.map((ind) => (
                <Link key={ind.id} to={ind.enlace} className="metric-card cc-metric-card" title={ind.label}>
                  <span className="metric-label">{ind.label}</span>
                  <ValorIndicador valor={ind.valor} disponible={ind.disponible} estado={ind.estado} />
                </Link>
              ))}
            </div>
          </section>

          <section className="panel compact-panel">
            <h2 className="section-title">Atención requerida</h2>
            {data.atencion_requerida.length === 0 ? (
              <p className="muted">No hay asuntos prioritarios pendientes.</p>
            ) : (
              <table className="data-table compact-table">
                <thead><tr><th>#</th><th>Tipo</th><th>Asunto</th><th>Origen</th><th></th></tr></thead>
                <tbody>
                  {data.atencion_requerida.map((item) => (
                    <tr key={`${item.tipo}-${item.prioridad}-${item.titulo}`}>
                      <td>{item.prioridad}</td>
                      <td>{item.tipo}</td>
                      <td>{item.titulo}</td>
                      <td>{item.origen}</td>
                      <td><Link to={item.enlace}>Ver</Link></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>

          <div className="cc-grid-2">
            <section className="panel compact-panel">
              <h2 className="section-title">Empleados IA</h2>
              {!data.empleados_ia ? (
                <p className="muted">Sin información disponible</p>
              ) : (
                <table className="data-table compact-table">
                  <thead><tr><th>Empleado</th><th>Estado</th><th>Última actividad</th><th></th></tr></thead>
                  <tbody>
                    {data.empleados_ia.items.slice(0, 8).map((e) => (
                      <tr key={e.id}>
                        <td>{e.nombre}</td>
                        <td>{e.estado}</td>
                        <td>{e.ultima_actividad ? new Date(e.ultima_actividad).toLocaleString("es-CO") : "—"}</td>
                        <td><Link to={e.enlace}>Detalle</Link></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </section>

            <section className="panel compact-panel">
              <h2 className="section-title">Oportunidades</h2>
              {!data.oportunidades?.disponible ? (
                <p className="muted">{data.oportunidades?.estado ?? "Sin información disponible"}</p>
              ) : (
                <>
                  <dl className="detail-grid">
                    <dt>Detectadas</dt><dd>{data.oportunidades.resumen?.oportunidades_detectadas ?? "—"}</dd>
                    <dt>En seguimiento</dt><dd>{data.oportunidades.estados_operativos?.seguimiento ?? "—"}</dd>
                    <dt>Materializadas</dt><dd>{data.oportunidades.resumen?.materializadas ?? "—"}</dd>
                    <dt>Valor potencial</dt><dd>{data.oportunidades.resumen?.valor_potencial_total ?? "—"}</dd>
                    <dt>Pend. aprobación</dt><dd>{data.oportunidades.resumen?.pendientes_aprobacion ?? "—"}</dd>
                  </dl>
                </>
              )}
              <p><Link to="/oportunidades">Ir al centro de oportunidades</Link></p>
            </section>
          </div>

          <div className="cc-grid-2">
            <section className="panel compact-panel">
              <h2 className="section-title">Impacto (línea base)</h2>
              {!data.impacto?.disponible ? (
                <p className="muted">{data.impacto?.estado ?? "Sin información disponible"}</p>
              ) : (
                <dl className="detail-grid">
                  <dt>Líneas base activas</dt><dd>{data.impacto.lineas_base_activas ?? "—"}</dd>
                  <dt>Mediciones</dt><dd>{data.impacto.mediciones ?? "—"}</dd>
                  <dt>Impactos reales</dt><dd>{data.impacto.impactos_reales ?? "—"}</dd>
                  <dt>Pend. validación</dt><dd>{data.impacto.mediciones_pendientes_validacion ?? "—"}</dd>
                  <dt>Con atribución</dt><dd>{data.impacto.impactos_con_atribucion ?? "—"}</dd>
                </dl>
              )}
              <p><Link to="/lineas-base">Ver líneas base</Link></p>
            </section>

            <section className="panel compact-panel">
              <h2 className="section-title">Costos y FinOps</h2>
              {!data.finops?.disponible ? (
                <p className="muted">Sin información disponible</p>
              ) : (
                <dl className="detail-grid">
                  <dt>Costo periodo</dt><dd>{data.finops.dashboard?.total_cost_label ?? "—"}</dd>
                  <dt>Valor generado</dt><dd>{data.finops.dashboard?.total_value_label ?? "—"}</dd>
                  <dt>Tokens periodo</dt><dd>{data.finops.tokens_periodo ?? "—"}</dd>
                  <dt>ROI</dt><dd>{data.finops.dashboard?.roi_label ?? "—"}</dd>
                </dl>
              )}
              <p><Link to="/costos-valor">Ver costos y valor</Link></p>
            </section>
          </div>

          <div className="cc-grid-2">
            <section className="panel compact-panel">
              <h2 className="section-title">Valor y retorno</h2>
              {!data.valor_retorno?.disponible ? (
                <p className="muted">{data.valor_retorno?.estado ?? "Sin información disponible"}</p>
              ) : (
                <dl className="detail-grid">
                  <dt>Valor esperado</dt><dd>{data.valor_retorno.valor_esperado ?? "—"}</dd>
                  <dt>Valor materializado</dt><dd>{data.valor_retorno.valor_materializado ?? "—"}</dd>
                  <dt>Valor atribuible</dt><dd>{data.valor_retorno.valor_atribuible ?? "—"}</dd>
                  <dt>Beneficio neto</dt><dd>{data.valor_retorno.beneficio_neto ?? "—"}</dd>
                  <dt>Retorno</dt><dd>{data.valor_retorno.retorno_porcentaje != null ? `${data.valor_retorno.retorno_porcentaje}%` : "—"}</dd>
                </dl>
              )}
              <p><Link to="/costos-valor">Ver valoración</Link></p>
            </section>
            <section className="panel compact-panel">
              <h2 className="section-title">Diagnóstico</h2>
              {!data.diagnostico?.disponible ? (
                <p className="muted">{data.diagnostico?.estado ?? "Sin información disponible"}</p>
              ) : (
                <dl className="detail-grid">
                  <dt>Diagnósticos activos</dt><dd>{data.diagnostico.diagnosticos_activos ?? "—"}</dd>
                  <dt>Hallazgos</dt><dd>{data.diagnostico.hallazgos ?? "—"}</dd>
                  <dt>Riesgos</dt><dd>{data.diagnostico.riesgos ?? "—"}</dd>
                  <dt>Oportunidades generadas</dt><dd>{data.diagnostico.oportunidades_generadas ?? "—"}</dd>
                </dl>
              )}
              <p><Link to="/diagnosticos">Ver diagnósticos</Link></p>
            </section>
          </div>

          <section className="panel compact-panel">
            <h2 className="section-title">Señales</h2>
            {!data.senales ? (
              <p className="muted">Sin información disponible</p>
            ) : (
              <>
                <dl className="detail-grid">
                  <dt>Total señales</dt><dd>{data.senales.total ?? "—"}</dd>
                  <dt>Sin procesar</dt><dd>{data.senales.sin_procesar ?? "—"}</dd>
                  <dt>Procesadas</dt><dd>{data.senales.procesadas ?? "—"}</dd>
                  <dt>Errores ingesta</dt><dd>{data.senales.errores_ingesta ?? "—"}</dd>
                  <dt>REAL</dt><dd>{data.senales.por_modo_ingesta?.REAL ?? "—"}</dd>
                  <dt>SINTÉTICO</dt><dd>{data.senales.por_modo_ingesta?.SINTETICO ?? "—"}</dd>
                  <dt>PRUEBA</dt><dd>{data.senales.por_modo_ingesta?.PRUEBA ?? "—"}</dd>
                </dl>
                <p><Link to="/senales">Ver señales</Link></p>
              </>
            )}
          </section>

          {data.cadena_ejecutiva && data.cadena_ejecutiva.length > 0 && (
            <section className="panel compact-panel">
              <h2 className="section-title">Cadena ejecutiva</h2>
              <table className="data-table compact-table">
                <thead><tr><th>Oportunidad</th><th>Etapas</th></tr></thead>
                <tbody>
                  {data.cadena_ejecutiva.map((cadena) => (
                    <tr key={cadena.oportunidad_id as string}>
                      <td><Link to={`/oportunidades/${cadena.oportunidad_id}`}>{String(cadena.titulo)}</Link></td>
                      <td>
                        {(cadena.etapas as Array<{ etapa: string; enlace: string }>).map((e) => (
                          <Link key={`${cadena.oportunidad_id}-${e.etapa}`} to={e.enlace} className="cc-chain-link">
                            {e.etapa}
                          </Link>
                        ))}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}

          <section className="panel compact-panel">
            <h2 className="section-title">Salud de la plataforma</h2>
            {data.salud_plataforma ? (
              <dl className="detail-grid">
                <dt>Estado API</dt><dd>{data.salud_plataforma.status}</dd>
                <dt>Base de datos</dt><dd>{data.salud_plataforma.database?.status ?? "—"}</dd>
                <dt>Schedulers</dt><dd>{data.salud_plataforma.schedulers?.status ?? "—"}</dd>
              </dl>
            ) : (
              <p className="muted">Sin información disponible</p>
            )}
          </section>
        </>
      )}
    </div>
  );
}
