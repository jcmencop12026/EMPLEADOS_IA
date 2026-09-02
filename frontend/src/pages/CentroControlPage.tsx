import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import type { CentroControlResumen, EvaluacionExpedienteSummary } from "../api";
import { fetchCentroControlResumen, fetchEvaluaciones } from "../api";
import { CentroControlCockpit } from "../components/centroControl/CentroControlCockpit";
import { CentroControlEmpresaPanel } from "../components/centroControl/CentroControlEmpresaPanel";
import { useOrganizationContext } from "../hooks/useOrganizationContext";
import { usePageAssistantContext } from "../hooks/usePageAssistantContext";
import { usePermissions } from "../hooks/usePermissions";
import { formatAuditAction, formatHealthStatus } from "../lib/labels";

const SECCIONES_DEFAULT = [
  { id: "resumen", label: "Resumen" },
  { id: "valor", label: "Valor" },
  { id: "operacion", label: "Operación" },
  { id: "ia_costos", label: "IA y costos" },
  { id: "implementacion", label: "Implementación" },
  { id: "salud", label: "Salud" },
] as const;

type SeccionId = (typeof SECCIONES_DEFAULT)[number]["id"];

function fmtNum(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "number") return v.toLocaleString("es-CO");
  return String(v);
}

function healthComponentStatus(salud: Record<string, unknown>, key: string): string | undefined {
  const components = salud.components as Record<string, { status?: string }> | undefined;
  return components?.[key]?.status ?? (salud[key] as { status?: string } | undefined)?.status;
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
  const { organizationQueryParam, effectiveOrganizationName, isViewingOtherOrganization } = useOrganizationContext();
  const [searchParams, setSearchParams] = useSearchParams();
  const [data, setData] = useState<CentroControlResumen | null>(null);
  const [evaluaciones, setEvaluaciones] = useState<EvaluacionExpedienteSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [periodo, setPeriodo] = useState("mtd");
  const [seccion, setSeccion] = useState<SeccionId>("resumen");
  const expedienteContext = searchParams.get("expediente") ?? "";

  usePageAssistantContext({ periodo, seccion, expediente_id: expedienteContext || undefined });

  useEffect(() => {
    if (!has("evaluacion.view")) return;
    fetchEvaluaciones()
      .then((r) => setEvaluaciones(r.items))
      .catch(() => undefined);
  }, [has]);

  const contextoLabel = useMemo(() => {
    if (!expedienteContext) return "Todas las empresas";
    const match = evaluaciones.find((e) => e.id === expedienteContext);
    return match ? `${match.entidad_nombre} · ${match.codigo}` : "Empresa seleccionada";
  }, [expedienteContext, evaluaciones]);

  function setExpedienteContext(id: string) {
    const next = new URLSearchParams(searchParams);
    if (id) next.set("expediente", id);
    else next.delete("expediente");
    setSearchParams(next, { replace: true });
  }

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchCentroControlResumen(periodo, organizationQueryParam)
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar"))
      .finally(() => setLoading(false));
  }, [periodo, organizationQueryParam]);

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
        <h1>Centro de Control</h1>
        <p className="muted">
          Una sola pantalla para operar, priorizar atención y conectar valor con la vista empresa
          {isViewingOtherOrganization && (
            <> · <strong>Organización: {effectiveOrganizationName}</strong></>
          )}
        </p>
        <div className="toolbar compact-toolbar cc-context-toolbar">
          <label className="cc-context-select">
            <span className="muted small">Contexto</span>
            <select
              value={expedienteContext}
              onChange={(e) => setExpedienteContext(e.target.value)}
              title="Contexto operativo"
            >
              <option value="">Todas las empresas / prospectos</option>
              {evaluaciones.map((ev) => (
                <option key={ev.id} value={ev.id}>
                  {ev.entidad_nombre} — {ev.codigo}
                </option>
              ))}
            </select>
          </label>
          <select value={periodo} onChange={(e) => setPeriodo(e.target.value)} title="Periodo">
            <option value="mtd">Mes actual</option>
            <option value="7d">Últimos 7 días</option>
            <option value="30d">Últimos 30 días</option>
          </select>
          {expedienteContext && (
            <>
              <Link to={`/presentacion/${expedienteContext}`} className="btn secondary small">Presentación</Link>
              <Link to={`/evaluaciones/${expedienteContext}?tab=vista-empresa`} className="btn secondary small">Ver como empresa</Link>
            </>
          )}
          <button type="button" onClick={load} disabled={loading}>Actualizar</button>
        </div>
        {expedienteContext && (
          <p className="muted small cc-context-banner">
            Vista de empresa: <strong>{contextoLabel}</strong> — la consola global permanece disponible al volver a «Todas».
          </p>
        )}
      </header>

      {loading && <p className="muted">Cargando centro de control…</p>}
      {error && <p className="error">{error}</p>}

      {expedienteContext && has("evaluacion.view") && (
        <CentroControlEmpresaPanel evaluacionId={expedienteContext} />
      )}

      {data && (
        <>
          {expedienteContext && (
            <h2 className="section-title cc-global-heading">Vista global del periodo</h2>
          )}
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
            <CentroControlCockpit data={data} periodo={periodo} />
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
                  <h2 className="section-title">Valoración económica</h2>
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
                  <h2 className="section-title">Comercial y propuestas</h2>
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
                  <h2 className="section-title">Mi Trabajo</h2>
                  {!data.mi_trabajo?.disponible ? (
                    <p className="muted">{data.mi_trabajo?.estado ?? "Sin información disponible"}</p>
                  ) : (
                    <dl className="detail-grid">
                      <dt>Pendientes</dt><dd>{data.mi_trabajo.pendientes ?? "—"}</dd>
                      <dt>Vencidas</dt><dd>{data.mi_trabajo.vencidas ?? "—"}</dd>
                      <dt>Requieren aprobación</dt><dd>{data.mi_trabajo.requieren_aprobacion ?? "—"}</dd>
                    </dl>
                  )}
                  <p><Link to="/trabajo">Ir a Mi Trabajo</Link></p>
                </section>

                <section className="panel compact-panel">
                  <h2 className="section-title">Auditor Empleados IA</h2>
                  {!data.auditor_empleados?.disponible ? (
                    <p className="muted">{data.auditor_empleados?.estado ?? "Sin información disponible"}</p>
                  ) : (
                    <>
                      <dl className="detail-grid">
                        <dt>Hallazgos abiertos</dt><dd>{data.auditor_empleados.hallazgos_abiertos ?? "—"}</dd>
                        <dt>Críticos</dt><dd>{data.auditor_empleados.criticos ?? "—"}</dd>
                        <dt>Requieren mejora</dt><dd>{data.auditor_empleados.requieren_mejora ?? "—"}</dd>
                      </dl>
                      <p className="muted">Auditor recomienda. Humano decide. Fábrica ejecuta.</p>
                    </>
                  )}
                  <p><Link to="/empleados/auditoria">Ver auditoría</Link></p>
                </section>
              </div>

              <div className="cc-grid-2">
                <section className="panel compact-panel">
                  <h2 className="section-title">Mesa de Ayuda</h2>
                  {!data.mb12_soporte?.disponible ? (
                    <p className="muted">{data.mb12_soporte?.estado ?? "Sin información disponible"}</p>
                  ) : (
                    <dl className="detail-grid">
                      <dt>Casos abiertos</dt><dd>{data.mb12_soporte.casos_abiertos ?? "—"}</dd>
                      <dt>Críticos</dt><dd>{data.mb12_soporte.casos_criticos ?? "—"}</dd>
                      <dt>Vencidos</dt><dd>{data.mb12_soporte.casos_vencidos ?? "—"}</dd>
                    </dl>
                  )}
                  <p><Link to="/soporte">Ir a Mesa de Ayuda</Link></p>
                </section>

                <section className="panel compact-panel">
                  <h2 className="section-title">Comunicaciones</h2>
                  {!data.mb11_comunicaciones?.disponible ? (
                    <p className="muted">{data.mb11_comunicaciones?.estado ?? "Sin información disponible"}</p>
                  ) : (
                    <dl className="detail-grid">
                      <dt>Enviados</dt><dd>{data.mb11_comunicaciones.enviados ?? "—"}</dd>
                      <dt>Pendientes</dt><dd>{data.mb11_comunicaciones.pendientes ?? "—"}</dd>
                      <dt>Fallidos</dt><dd>{data.mb11_comunicaciones.fallidos ?? "—"}</dd>
                      <dt>Canales degradados</dt><dd>{data.mb11_comunicaciones.canales_degradados ?? "—"}</dd>
                    </dl>
                  )}
                  <p><Link to="/comunicaciones">Ir a Comunicaciones</Link></p>
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
                <section className="panel compact-panel">
                  <h2 className="section-title">Integraciones</h2>
                  <p className="muted">Conectores, cableado y trazabilidad de integraciones empresariales.</p>
                  <p><Link to="/integraciones">Ir a integraciones</Link></p>
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
                  <h2 className="section-title">Planificador de consumo</h2>
                  {!data.mb07_planificador?.disponible ? (
                    <p className="muted">{data.mb07_planificador?.estado ?? "Sin información disponible"}</p>
                  ) : (
                    <dl className="detail-grid">
                      <dt>Consumo real</dt><dd>{fmtNum(data.mb07_planificador.consumo_real)}</dd>
                      <dt>Proyección mes</dt><dd>{fmtNum(data.mb07_planificador.consumo_proyectado)}</dd>
                      <dt>Presupuesto</dt><dd>{fmtNum(data.mb07_planificador.presupuesto_limite)}</dd>
                      <dt>Utilización</dt><dd>{data.mb07_planificador.presupuesto_utilizacion_pct != null ? `${data.mb07_planificador.presupuesto_utilizacion_pct}%` : "—"}</dd>
                      <dt>Riesgo capacidad</dt><dd>{String(data.mb07_planificador.capacidad_riesgo ?? "—")}</dd>
                    </dl>
                  )}
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
                  <h2 className="section-title">Proveedores IA</h2>
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
                      <dt>Estado API</dt><dd>{formatHealthStatus(data.salud_plataforma.status as string)}</dd>
                      <dt>Base de datos</dt><dd>{formatHealthStatus(healthComponentStatus(data.salud_plataforma as Record<string, unknown>, "database"))}</dd>
                      <dt>Schedulers</dt><dd>{formatHealthStatus(healthComponentStatus(data.salud_plataforma as Record<string, unknown>, "schedulers"))}</dd>
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
                  <h2 className="section-title">Continuidad y riesgos</h2>
                  {!data.continuidad?.disponible ? (
                    <p className="muted">{data.continuidad?.estado ?? "Sin incidentes registrados"}</p>
                  ) : (
                    <dl className="detail-grid">
                      <dt>Degradados</dt><dd>{data.continuidad.servicios_degradados ?? "—"}</dd>
                      <dt>Incidentes abiertos</dt><dd>{data.continuidad.incidentes_abiertos ?? "—"}</dd>
                      <dt>Backups fallidos</dt><dd>{data.continuidad.backups_fallidos ?? "—"}</dd>
                    </dl>
                  )}
                  <p><Link to="/continuidad">Ver continuidad</Link></p>
                </section>

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
                            <td>{formatAuditAction(row.accion)}</td>
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
