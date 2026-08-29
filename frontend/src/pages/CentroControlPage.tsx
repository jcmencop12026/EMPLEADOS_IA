import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { CentroControlResumen } from "../api";
import { fetchCentroControlResumen } from "../api";
import { usePermissions } from "../hooks/usePermissions";

const SECCIONES_DEFAULT = [
  { id: "resumen", label: "Resumen" },
  { id: "valor", label: "Valor" },
  { id: "operacion", label: "Operación" },
  { id: "ia_costos", label: "IA y costos" },
  { id: "implementacion", label: "Implementación" },
  { id: "salud", label: "Salud" },
] as const;

type SeccionId = (typeof SECCIONES_DEFAULT)[number]["id"];

function ValorIndicador({ valor, disponible, estado }: { valor: unknown; disponible: boolean; estado?: string | null }) {
  if (!disponible) return <span className="muted">{estado ?? "Sin información disponible"}</span>;
  if (valor === null || valor === undefined) return <span className="muted">Sin información disponible</span>;
  return <strong>{String(valor)}</strong>;
}

function fmtNum(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "number") return v.toLocaleString("es-CO");
  return String(v);
}

function SemanticBadge({ tipo }: { tipo: string }) {
  const cls = tipo.toLowerCase();
  if (cls === "hecho") return <span className="semantic-badge hecho">HECHO</span>;
  if (cls === "inferencia") return <span className="semantic-badge inferencia">INFERENCIA</span>;
  if (cls === "recomendacion") return <span className="semantic-badge recomendacion">RECOMENDACIÓN</span>;
  return <span className="semantic-badge">{tipo}</span>;
}

export function CentroControlPage() {
  const { has } = usePermissions();
  const [data, setData] = useState<CentroControlResumen | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [periodo, setPeriodo] = useState("mtd");
  const [seccion, setSeccion] = useState<SeccionId>("resumen");

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

  const secciones = data?.secciones?.length ? data.secciones : SECCIONES_DEFAULT;
  const valor = data?.valor_consolidado ?? data?.resumen_ejecutivo?.valor;

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
          <nav className="tab-bar compact-tabs" aria-label="Secciones ejecutivas">
            {secciones.map((s) => (
              <button
                key={s.id}
                type="button"
                className={`tab-btn ${seccion === s.id ? "active" : ""}`}
                onClick={() => setSeccion(s.id as SeccionId)}
              >
                {s.label}
              </button>
            ))}
          </nav>

          {seccion === "resumen" && (
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

              <section className="panel compact-panel">
                <h2 className="section-title">¿Por qué está pasando?</h2>
                <p className="muted cc-explicacion-nota">
                  {data.explicacion?.nota_causalidad ?? "Las correlaciones no implican causalidad demostrada."}
                </p>
                {!data.explicacion?.disponible ? (
                  <p className="muted">{data.explicacion?.estado ?? "Diagnóstico no disponible"}</p>
                ) : (
                  <table className="data-table compact-table">
                    <thead>
                      <tr><th>Situación</th><th>Causa / acción</th><th>Certeza</th><th>Evidencia</th><th></th></tr>
                    </thead>
                    <tbody>
                      {(data.explicacion.elementos ?? []).slice(0, 8).map((el) => (
                        <tr key={el.id}>
                          <td>
                            <span className={`cc-tag cc-tag-${el.tipo_contenido.toLowerCase()}`}>{el.tipo_contenido}</span>
                            <div>{el.situacion ?? "—"}</div>
                          </td>
                          <td>{el.causa ?? "—"}</td>
                          <td>{el.certeza ?? "—"}</td>
                          <td>{el.evidencia?.resumen ?? el.evidencia?.identificador ?? "—"}</td>
                          <td>{el.enlace?.startsWith("/") ? <Link to={el.enlace}>Detalle</Link> : "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
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
            </>
          )}

          {seccion === "valor" && (
            <>
              <section className="panel compact-panel">
                <h2 className="section-title">Valor por naturaleza</h2>
                <p className="muted potential-excluded">{valor?.nota_potencial ?? "El valor potencial no se suma al valor realizado."}</p>
                <div className="value-nature-grid">
                  <div className="value-nature-card verified">
                    <div className="value-nature-head">Verificado <SemanticBadge tipo="hecho" /></div>
                    <span className="value-nature-amount">{fmtNum(valor?.verificado)}</span>
                  </div>
                  <div className="value-nature-card estimated">
                    <div className="value-nature-head">Estimado <SemanticBadge tipo="inferencia" /></div>
                    <span className="value-nature-amount">{fmtNum(valor?.estimado)}</span>
                  </div>
                  <div className="value-nature-card potential">
                    <div className="value-nature-head">Potencial <SemanticBadge tipo="inferencia" /></div>
                    <span className="value-nature-amount">{fmtNum(valor?.potencial)}</span>
                  </div>
                  <div className="value-nature-card price-base">
                    <div className="value-nature-head">Realizado (verif. + estim.)</div>
                    <span className="value-nature-amount">{fmtNum(valor?.realizado)}</span>
                  </div>
                </div>
              </section>

              <div className="cc-grid-2">
                <section className="panel compact-panel">
                  <h2 className="section-title">Valoración 1210</h2>
                  {!data.valor_retorno?.disponible ? (
                    <p className="muted">{data.valor_retorno?.estado ?? "Sin información disponible"}</p>
                  ) : (
                    <dl className="detail-grid">
                      <dt>Verificado</dt><dd>{fmtNum(data.valor_retorno.valor_verificado)}</dd>
                      <dt>Estimado</dt><dd>{fmtNum(data.valor_retorno.valor_estimado)}</dd>
                      <dt>Potencial</dt><dd className="potential-excluded">{fmtNum(data.valor_retorno.valor_potencial)}</dd>
                      <dt>Retorno</dt><dd>{data.valor_retorno.retorno_porcentaje != null ? `${data.valor_retorno.retorno_porcentaje}%` : "—"}</dd>
                    </dl>
                  )}
                  <p><Link to="/costos-valor">Ver valoración</Link></p>
                </section>

                <section className="panel compact-panel">
                  <h2 className="section-title">Comercial 1280</h2>
                  {!data.comercial?.disponible ? (
                    <p className="muted">{data.comercial?.estado ?? "Sin información disponible"}</p>
                  ) : (
                    <dl className="detail-grid">
                      <dt>Propuestas</dt><dd>{data.comercial.propuestas_total ?? "—"}</dd>
                      <dt>Verificado</dt><dd>{fmtNum(data.comercial.valor_verificado)}</dd>
                      <dt>Estimado</dt><dd>{fmtNum(data.comercial.valor_estimado)}</dd>
                      <dt>Potencial</dt><dd className="potential-excluded">{fmtNum(data.comercial.valor_potencial)}</dd>
                      <dt>ROI promedio</dt><dd>{data.comercial.roi_promedio != null ? `${data.comercial.roi_promedio}%` : "—"}</dd>
                      <dt>Payback</dt><dd>{data.comercial.payback_promedio_meses != null ? `${data.comercial.payback_promedio_meses} meses` : "—"}</dd>
                      {data.comercial.margen_promedio_pct != null && (
                        <><dt>Margen</dt><dd>{data.comercial.margen_promedio_pct}%</dd></>
                      )}
                      {data.comercial.margen_restringido && (
                        <><dt>Margen</dt><dd className="muted">No disponible (permiso requerido)</dd></>
                      )}
                    </dl>
                  )}
                  <p><Link to="/comercial">Ver comercial</Link></p>
                </section>
              </div>
            </>
          )}

          {seccion === "operacion" && (
            <>
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
                    <dl className="detail-grid">
                      <dt>Detectadas</dt><dd>{data.oportunidades.resumen?.oportunidades_detectadas ?? "—"}</dd>
                      <dt>En seguimiento</dt><dd>{data.oportunidades.estados_operativos?.seguimiento ?? "—"}</dd>
                      <dt>Materializadas</dt><dd>{data.oportunidades.resumen?.materializadas ?? "—"}</dd>
                      <dt>Pend. aprobación</dt><dd>{data.oportunidades.resumen?.pendientes_aprobacion ?? "—"}</dd>
                    </dl>
                  )}
                  <p><Link to="/oportunidades">Ir a oportunidades</Link></p>
                </section>
              </div>

              <div className="cc-grid-2">
                <section className="panel compact-panel">
                  <h2 className="section-title">Línea base e impacto</h2>
                  {!data.impacto?.disponible ? (
                    <p className="muted">{data.impacto?.estado ?? "Sin información disponible"}</p>
                  ) : (
                    <dl className="detail-grid">
                      <dt>Líneas base activas</dt><dd>{data.impacto.lineas_base_activas ?? "—"}</dd>
                      <dt>Mediciones</dt><dd>{data.impacto.mediciones ?? "—"}</dd>
                      <dt>Impactos reales</dt><dd>{data.impacto.impactos_reales ?? "—"}</dd>
                      <dt>Pend. validación</dt><dd>{data.impacto.mediciones_pendientes_validacion ?? "—"}</dd>
                    </dl>
                  )}
                  <p><Link to="/lineas-base">Ver líneas base</Link></p>
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
                    </dl>
                  )}
                  <p><Link to="/diagnosticos">Ver diagnósticos</Link></p>
                </section>
              </div>

              <div className="cc-grid-2">
                <section className="panel compact-panel">
                  <h2 className="section-title">Señales internas</h2>
                  <dl className="detail-grid">
                    <dt>Total</dt><dd>{data.senales?.total ?? "—"}</dd>
                    <dt>Sin procesar</dt><dd>{data.senales?.sin_procesar ?? "—"}</dd>
                    <dt>Errores ingesta</dt><dd>{data.senales?.errores_ingesta ?? "—"}</dd>
                  </dl>
                  <p><Link to="/senales">Ver señales</Link></p>
                </section>

                <section className="panel compact-panel">
                  <h2 className="section-title">Inteligencia externa</h2>
                  {!data.inteligencia_externa?.disponible ? (
                    <p className="muted">{data.inteligencia_externa?.estado ?? "Sin información disponible"}</p>
                  ) : (
                    <dl className="detail-grid">
                      <dt>Fuentes activas</dt><dd>{data.inteligencia_externa.fuentes_activas ?? "—"}</dd>
                      <dt>Sin validar</dt><dd>{data.inteligencia_externa.sin_validar ?? "—"}</dd>
                      <dt>Riesgos abiertos</dt><dd>{data.inteligencia_externa.riesgos_abiertos ?? "—"}</dd>
                    </dl>
                  )}
                  <p><Link to="/inteligencia-externa">Ver inteligencia externa</Link></p>
                </section>
              </div>

              <section className="panel compact-panel">
                <h2 className="section-title">Actividad reciente</h2>
                {!data.actividad_reciente?.length ? (
                  <p className="muted">Sin actividad operativa reciente</p>
                ) : (
                  <table className="data-table compact-table">
                    <thead><tr><th>Evento</th><th>Fecha</th><th></th></tr></thead>
                    <tbody>
                      {data.actividad_reciente.slice(0, 8).map((ev) => (
                        <tr key={ev.id}>
                          <td>{ev.tipo}</td>
                          <td>{ev.fecha ? new Date(ev.fecha).toLocaleString("es-CO") : "—"}</td>
                          <td>{ev.enlace ? <Link to={ev.enlace}>Ver</Link> : "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </section>
            </>
          )}

          {seccion === "ia_costos" && (
            <>
              <div className="cc-grid-2">
                <section className="panel compact-panel">
                  <h2 className="section-title">FinOps</h2>
                  {!data.finops?.disponible ? (
                    <p className="muted">Sin información disponible</p>
                  ) : (
                    <dl className="detail-grid">
                      <dt>Costo periodo</dt><dd>{data.finops.dashboard?.total_cost_label ?? "—"}</dd>
                      <dt>Valor generado</dt><dd>{data.finops.dashboard?.total_value_label ?? "—"}</dd>
                      <dt>Tokens</dt><dd>{data.finops.tokens_periodo ?? "—"}</dd>
                      <dt>ROI</dt><dd>{data.finops.dashboard?.roi_label ?? "—"}</dd>
                    </dl>
                  )}
                  <p><Link to="/costos-valor">Ver costos y valor</Link></p>
                </section>

                <section className="panel compact-panel">
                  <h2 className="section-title">TCO</h2>
                  {!data.tco?.disponible ? (
                    <p className="muted">{data.tco?.estado ?? "Sin información disponible"}</p>
                  ) : (
                    <dl className="detail-grid">
                      <dt>Inversión mensual</dt><dd>{fmtNum(data.tco.inversion_total)}</dd>
                      <dt>Costos IA (FinOps)</dt><dd>{fmtNum(data.tco.finops_ia)}</dd>
                      <dt>Alertas</dt><dd>{data.tco.alertas ?? "—"}</dd>
                      {data.tco.margen_pct != null && <><dt>Margen</dt><dd>{data.tco.margen_pct}%</dd></>}
                      {data.tco.margen_restringido && <><dt>Margen</dt><dd className="muted">No disponible</dd></>}
                    </dl>
                  )}
                  <p><Link to="/tco">Ver TCO</Link></p>
                </section>
              </div>

              <div className="cc-grid-2">
                <section className="panel compact-panel">
                  <h2 className="section-title">Proveedores IA (1270)</h2>
                  {!data.multiproveedor?.disponible ? (
                    <p className="muted">{data.multiproveedor?.estado ?? "Sin información disponible"}</p>
                  ) : (
                    <>
                      <dl className="detail-grid">
                        <dt>Proveedores</dt><dd>{data.multiproveedor.proveedores_total ?? "—"}</dd>
                        <dt>Degradados</dt><dd>{data.multiproveedor.proveedores_degradados ?? "—"}</dd>
                        <dt>Inferencias periodo</dt><dd>{data.multiproveedor.observabilidad?.total_inferencias ?? "—"}</dd>
                        <dt>Tasa éxito</dt><dd>{data.multiproveedor.observabilidad?.tasa_exito != null ? `${data.multiproveedor.observabilidad.tasa_exito}%` : "—"}</dd>
                      </dl>
                      <table className="data-table compact-table">
                        <thead><tr><th>Proveedor</th><th>Estado</th><th>Detalle</th></tr></thead>
                        <tbody>
                          {(data.multiproveedor.salud ?? []).slice(0, 5).map((p) => (
                            <tr key={p.provider_id}>
                              <td>{p.nombre}</td>
                              <td>{p.estado}</td>
                              <td>{p.detalle}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </>
                  )}
                  <p><Link to="/administracion/proveedores-ia">Administrar proveedores</Link></p>
                </section>

                <section className="panel compact-panel">
                  <h2 className="section-title">Consumo por proveedor</h2>
                  {!data.llm?.proveedores?.length ? (
                    <p className="muted">Sin proveedores configurados</p>
                  ) : (
                    <table className="data-table compact-table">
                      <thead><tr><th>Proveedor</th><th>Estado</th><th>Errores 24h</th><th>Tokens 24h</th></tr></thead>
                      <tbody>
                        {data.llm.proveedores.slice(0, 5).map((p) => (
                          <tr key={p.id}>
                            <td>{p.nombre}</td>
                            <td>{p.estado ?? "—"}</td>
                            <td>{p.errores_24h}</td>
                            <td>{p.tokens_24h ?? "—"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </section>
              </div>
            </>
          )}

          {seccion === "implementacion" && (
            <section className="panel compact-panel">
              <h2 className="section-title">Implementación y éxito del cliente</h2>
              {!data.implementacion?.disponible ? (
                <p className="muted">{data.implementacion?.estado ?? "Sin información disponible"}</p>
              ) : (
                <>
                  <dl className="detail-grid">
                    <dt>Proyectos activos</dt><dd>{data.implementacion.proyectos_activos ?? "—"}</dd>
                    <dt>Total proyectos</dt><dd>{data.implementacion.proyectos_total ?? "—"}</dd>
                    <dt>Hitos en riesgo</dt><dd>{data.implementacion.hitos_en_riesgo ?? "—"}</dd>
                    <dt>Riesgos abiertos</dt><dd>{data.implementacion.riesgos_abiertos ?? "—"}</dd>
                  </dl>
                  {data.implementacion.recientes && data.implementacion.recientes.length > 0 && (
                    <table className="data-table compact-table">
                      <thead><tr><th>Código</th><th>Título</th><th>Estado</th><th>Avance</th></tr></thead>
                      <tbody>
                        {data.implementacion.recientes.slice(0, 5).map((p) => (
                          <tr key={p.id}>
                            <td>{p.codigo}</td>
                            <td><Link to={`/implementacion/${p.id}`}>{p.titulo}</Link></td>
                            <td>{p.estado}</td>
                            <td>{p.avance_pct != null ? `${p.avance_pct}%` : "—"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </>
              )}
              <p><Link to="/implementacion">Ver implementación</Link></p>
            </section>
          )}

          {seccion === "salud" && (
            <>
              <div className="cc-grid-2">
                <section className="panel compact-panel">
                  <h2 className="section-title">Salud de la plataforma</h2>
                  {data.salud_plataforma ? (
                    <dl className="detail-grid">
                      <dt>Estado API</dt><dd>{data.salud_plataforma.status as string}</dd>
                      <dt>Base de datos</dt><dd>{(data.salud_plataforma.database as { status?: string })?.status ?? "—"}</dd>
                      <dt>Schedulers</dt><dd>{(data.salud_plataforma.schedulers as { status?: string })?.status ?? "—"}</dd>
                    </dl>
                  ) : (
                    <p className="muted">Sin información disponible</p>
                  )}
                </section>

                <section className="panel compact-panel">
                  <h2 className="section-title">Aprendizaje</h2>
                  {!data.aprendizaje?.disponible ? (
                    <p className="muted">{data.aprendizaje?.estado ?? "Sin información disponible"}</p>
                  ) : (
                    <dl className="detail-grid">
                      <dt>Ciclos</dt><dd>{data.aprendizaje.ciclos_total ?? "—"}</dd>
                      <dt>Patrones</dt><dd>{data.aprendizaje.patrones_detectados ?? "—"}</dd>
                      <dt>Recalibraciones pendientes</dt><dd>{data.aprendizaje.recalibraciones_pendientes ?? "—"}</dd>
                    </dl>
                  )}
                  <p><Link to="/aprendizaje">Ver aprendizaje</Link></p>
                </section>
              </div>

              <div className="cc-grid-2">
                <section className="panel compact-panel">
                  <h2 className="section-title">Optimización</h2>
                  {!data.optimizacion?.disponible ? (
                    <p className="muted">{data.optimizacion?.estado ?? "Sin información disponible"}</p>
                  ) : (
                    <>
                      <dl className="detail-grid">
                        <dt>Recomendaciones</dt><dd>{data.optimizacion.recomendaciones_total ?? "—"}</dd>
                        <dt>Pendientes</dt><dd>{data.optimizacion.pendientes_aprobacion ?? "—"}</dd>
                        <dt>Aprobadas</dt><dd>{data.optimizacion.aprobadas ?? "—"}</dd>
                      </dl>
                      <p className="muted"><SemanticBadge tipo="recomendacion" /> Las recomendaciones no son hechos.</p>
                    </>
                  )}
                  <p><Link to="/optimizacion">Ver optimización</Link></p>
                </section>

                <section className="panel compact-panel">
                  <h2 className="section-title">Auditoría reciente</h2>
                  {!data.auditoria_reciente?.length ? (
                    <p className="muted">Sin registros recientes</p>
                  ) : (
                    <table className="data-table compact-table">
                      <thead><tr><th>Acción</th><th>Actor</th><th>Fecha</th></tr></thead>
                      <tbody>
                        {data.auditoria_reciente.slice(0, 6).map((row) => (
                          <tr key={row.id}>
                            <td>{row.accion}</td>
                            <td>{row.actor ?? "—"}</td>
                            <td>{row.fecha ? new Date(row.fecha).toLocaleString("es-CO") : "—"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                  <p><Link to="/auditoria">Ver auditoría</Link></p>
                </section>
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}
