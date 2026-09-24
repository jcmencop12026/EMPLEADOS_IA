import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  fetchEvaluacion,
  fetchEvaluacionImpacto,
  type EvaluacionExpedienteDetail,
} from "../../api";
import { SiguienteAccionPanel } from "../evaluacion/SiguienteAccionPanel";
import { CadenaAnaliticaPanel } from "../evaluacion/CadenaAnaliticaPanel";
import { ExecutiveCard, KpiStrip, StatusBadge } from "../v1";
import { formatValorPotencialKpi } from "../../lib/formatKpiValue";
import { ImpactoGrafico } from "../evaluacion/ImpactoGrafico";
import { CONFIANZA, ESTADO_EXPEDIENTE, label, labelNivelEvaluacion } from "../../lib/evaluacionLabels";
import { cabinaTabPath, mapSiguienteAccionToCabinaTab } from "../../lib/siguienteAccionTabMap";
import { narrativaCampo } from "../../lib/informeNarrativa";

type Props = { evaluacionId: string };

function estimarAvanceAnalitico(infoPct: number, hallazgos: number, oportunidades: number) {
  if (infoPct < 100) {
    const avance = Math.max(5, Math.min(35, Math.round(infoPct * 0.35)));
    return { avance, estado: "Recibiendo información", eta: "Pendiente completar información mínima" };
  }
  if (hallazgos === 0) return { avance: 55, estado: "Procesando información", eta: "Aprox. 6–10 min" };
  if (oportunidades === 0) return { avance: 78, estado: "Analizando hallazgos", eta: "Aprox. 2–5 min" };
  return { avance: 100, estado: "Primera salida disponible", eta: "Resultados listos" };
}

export function CentroControlEmpresaPanel({ evaluacionId }: Props) {
  const navigate = useNavigate();
  const [exp, setExp] = useState<EvaluacionExpedienteDetail | null>(null);
  const [impacto, setImpacto] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([fetchEvaluacion(evaluacionId), fetchEvaluacionImpacto(evaluacionId).catch(() => null)])
      .then(([detail, imp]) => { setExp(detail); setImpacto(imp); setError(null); })
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar expediente"))
      .finally(() => setLoading(false));
  }, [evaluacionId]);

  useEffect(() => { load(); }, [load]);

  const entidadesRelacionadas = useMemo(() => {
    if (!exp) return [];
    const items: Array<{ nombre: string; tipo: string; enlace: string }> = [];
    const sector = String((exp as Record<string, unknown>).sector ?? "").toLowerCase();
    if (sector.includes("salud")) items.push({ nombre: exp.entidad_nombre, tipo: "IPS / entidad salud", enlace: `/evaluaciones/${evaluacionId}?tab=diagnostico` });
    for (const info of exp.informacion ?? []) {
      const pregunta = String(info.etiqueta ?? info.campo ?? "").toLowerCase();
      const respuesta = String(info.respuesta ?? "").trim();
      if (!respuesta) continue;
      if (pregunta.includes("ips") || pregunta.includes("unidad") || pregunta.includes("sede") || pregunta.includes("entidad")) {
        items.push({ nombre: respuesta, tipo: pregunta.includes("ips") ? "IPS" : "Unidad / proceso", enlace: `/evaluaciones/${evaluacionId}?tab=diagnostico` });
      }
    }
    const seen = new Set<string>();
    return items.filter((e) => { const key = `${e.nombre}-${e.tipo}`; if (seen.has(key)) return false; seen.add(key); return true; });
  }, [exp, evaluacionId]);

  if (loading && !exp) return <p className="muted">Cargando contexto de empresa…</p>;
  if (error && !exp) return <p className="error">{error}</p>;
  if (!exp) return null;

  const oportunidades = exp.hallazgos.filter((h) => h.opportunity_id).length;
  const indicadores = (impacto?.indicadores as Array<Record<string, unknown>> | undefined) ?? [];
  const valorKpi = formatValorPotencialKpi(exp.valor_potencial);
  const infoFaltante = Math.max(0, 100 - (exp.porcentaje_informacion ?? 0));
  const procesamiento = estimarAvanceAnalitico(exp.porcentaje_informacion ?? 0, exp.hallazgos.length, oportunidades);

  return (
    <div className="cc-empresa-panel">
      <ExecutiveCard
        className="cc-empresa-hero"
        title={`${exp.entidad_nombre} — ${exp.codigo} · ${exp.titulo}`}
        subtitle=""
        demo={exp.entidad_nombre?.startsWith("[DEMO]")}
        actions={<Link to={`/evaluaciones/${evaluacionId}`} className="btn primary small" title="Abre la cabina completa para ejecutar diagnóstico, valoración y acciones de esta empresa" data-help="Abre el puesto operativo completo de esta empresa. Úselo para pasar del resumen ejecutivo a diagnóstico, valoración, decisiones y acciones con toda la evidencia disponible.">Abrir cabina</Link>}
      >
        <div className="cc-empresa-hero-band">
          <div className="v1-empresa-meta">
            <StatusBadge label={label(ESTADO_EXPEDIENTE, exp.estado)} tone="info" />
            <span className="muted small">Puesto de mando — empresa seleccionada</span>
          </div>
        </div>
        <KpiStrip className="v1-empresa-kpis" items={[
          { id: "info", label: "Información completada", value: `${exp.porcentaje_informacion}%` },
          { id: "conf", label: "Confianza", value: label(CONFIANZA, exp.confianza_global) },
          { id: "opp", label: "Oportunidades", value: oportunidades },
          { id: "hall", label: "Hallazgos", value: exp.hallazgos.length },
          { id: "valor", label: "Valor potencial", value: valorKpi.main, unit: valorKpi.unit, hint: String(exp.valor_potencial ?? "").includes("DEMO") ? "DEMO — DATOS SIMULADOS" : undefined, tone: "value", wide: true },
          { id: "nivel", label: "Nivel", value: labelNivelEvaluacion(exp.nivel) },
        ]} />
        <div className="cc-processing-meter" data-help="Indicador interno de avance analítico. Combina completitud de información y resultados ya generados para estimar en qué punto del procesamiento está EIAAX. Se usa para gestionar la reunión y no se muestra al cliente.">
          <div className="cc-processing-meter__head">
            <div><span className="cc-processing-meter__eyebrow">Procesamiento EIAAX</span><strong>{procesamiento.estado}</strong></div>
            <div className="cc-processing-meter__numbers"><strong>{procesamiento.avance}%</strong><span>{procesamiento.eta}</span></div>
          </div>
          <div className="cc-processing-meter__track" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={procesamiento.avance} aria-label="Avance estimado del procesamiento EIAAX">
            <span style={{ width: `${procesamiento.avance}%` }} />
          </div>
          <p>Indicador aproximado para gestión interna de la reunión. No visible para la empresa.</p>
        </div>
      </ExecutiveCard>

      <section className="cc-resumen-ejecutivo-grid" aria-label="Resumen ejecutivo de la empresa">
        <article className="cc-resumen-card"><h3 className="cc-resumen-card__title">Qué sabemos</h3><p className="cc-resumen-card__value">{exp.porcentaje_informacion}% información</p><p className="cc-resumen-card__hint">{exp.hallazgos.length} hallazgos · confianza {label(CONFIANZA, exp.confianza_global)}</p></article>
        <article className="cc-resumen-card"><h3 className="cc-resumen-card__title">Qué falta</h3><p className="cc-resumen-card__value">{infoFaltante > 0 ? `${infoFaltante}% por completar` : "Completo"}</p><p className="cc-resumen-card__hint">{exp.necesidad ? String(exp.necesidad).slice(0, 72) : "Sin necesidad registrada"}</p></article>
        <article className="cc-resumen-card"><h3 className="cc-resumen-card__title">Lo que encontró EIAAX</h3><p className="cc-resumen-card__value">{exp.hallazgos.length} hallazgos</p><p className="cc-resumen-card__hint">{oportunidades} oportunidades vinculadas</p></article>
        <article className="cc-resumen-card cc-resumen-card--action"><h3 className="cc-resumen-card__title">Siguiente acción</h3><p className="cc-resumen-card__value">{label(ESTADO_EXPEDIENTE, exp.estado)}</p><p className="cc-resumen-card__hint">Continúe con la recomendación operativa de abajo.</p></article>
      </section>

      <div className="cc-grid-2 cc-prioridad-operativa">
        <section className="panel compact-panel">
          <SiguienteAccionPanel expedienteId={evaluacionId} onRefresh={load} onNavigateTab={(p) => { const tab = mapSiguienteAccionToCabinaTab(p); if (tab) navigate(cabinaTabPath(evaluacionId, tab)); }} />
        </section>
        <section className="panel compact-panel">
          <h2 className="section-title">Resumen ejecutivo</h2>
          <dl className="detail-grid compact"><dt>Problema</dt><dd>{exp.necesidad ?? "—"}</dd><dt>Objetivo</dt><dd>{exp.objetivo ?? "—"}</dd><dt>Área / proceso</dt><dd>{exp.area_proceso ?? "—"}</dd></dl>
          <p className="muted small">El diagnóstico, la solución IA y la operación se gestionan desde la cabina sin duplicar entidades.</p>
          <p><Link to={`/evaluaciones/${evaluacionId}`} title="Abre todos los módulos operativos de esta empresa">Ir a cabina completa</Link>{" · "}<Link to={`/evaluaciones/${evaluacionId}?tab=resultados`} title="Muestra oportunidades, resultados e impacto registrado">Oportunidades y resultados</Link></p>
        </section>
      </div>

      <details className="panel compact-panel cc-secondary-detail">
        <summary title="Despliega la cadena analítica completa cuando necesite revisar el detalle del proceso" data-help="Expande la trazabilidad analítica de esta empresa. Úsela cuando necesite revisar cómo EIAAX pasó de evidencia y diagnóstico a hallazgos, oportunidades y recomendaciones.">Cadena analítica · ver detalle</summary>
        <CadenaAnaliticaPanel expedienteId={evaluacionId} compact />
      </details>

      {entidadesRelacionadas.length > 0 && (
        <details className="panel compact-panel cc-secondary-detail">
          <summary title="Muestra unidades, IPS o procesos relacionados con la empresa seleccionada">Entidades relacionadas · {entidadesRelacionadas.length}</summary>
          <ul className="cc-entidades-list">{entidadesRelacionadas.map((ent) => <li key={`${ent.tipo}-${ent.nombre}`}><Link to={ent.enlace} className="cc-entidad-link"><strong>{ent.nombre}</strong><span className="muted small">{ent.tipo}</span></Link><span className="cc-entidad-actions"><Link to={ent.enlace} className="btn small secondary" title="Abre la información disponible de esta entidad">Información</Link><Link to={`/evaluaciones/${evaluacionId}?tab=diagnostico`} className="btn small secondary" title="Abre el diagnóstico asociado a esta entidad">Diagnóstico</Link><Link to="/directorio" className="btn small secondary" title="Abre los empleados IA disponibles">Empleados</Link><Link to="/operaciones" className="btn small secondary" title="Abre la operación y ejecuciones relacionadas">Operaciones</Link></span></li>)}</ul>
        </details>
      )}

      {indicadores.length > 0 && (
        <details className="panel compact-panel cc-tablero-empresa cc-secondary-detail">
          <summary title="Despliega indicadores, interpretación y evolución de resultados">Tablero empresarial · indicadores</summary>
          <div className="cc-tablero-head"><h2 className="section-title">Indicadores e interpretación</h2><Link to={`/evaluaciones/${evaluacionId}?tab=resultados`} className="btn small secondary" title="Abre el análisis detallado de resultados">Profundizar</Link></div>
          {exp.entidad_nombre?.startsWith("[DEMO]") && <p className="demo-banner" role="status">DEMO — DATOS SIMULADOS — proyecciones no equivalen a verificación real.</p>}
          <dl className="detail-grid compact cc-interpretacion-strip"><dt>Qué ocurrió</dt><dd>{narrativaCampo((impacto?.interpretacion as Record<string, unknown> | undefined)?.que_ocurrio)}</dd><dt>Por qué</dt><dd>{narrativaCampo((impacto?.interpretacion as Record<string, unknown> | undefined)?.por_que)}</dd><dt>Requiere atención</dt><dd>{narrativaCampo((impacto?.interpretacion as Record<string, unknown> | undefined)?.requiere_atencion)}</dd><dt>Oportunidad</dt><dd>{narrativaCampo((impacto?.interpretacion as Record<string, unknown> | undefined)?.oportunidad)}</dd><dt>Recomendación EIAAX</dt><dd>{narrativaCampo((impacto?.interpretacion as Record<string, unknown> | undefined)?.recomendacion)}</dd></dl>
          <table className="data-table compact-table impacto-indicadores-table"><thead><tr><th>Indicador</th><th>Antes</th><th>Proyectado</th><th>Real</th><th>Evolución</th></tr></thead><tbody>{indicadores.slice(0, 6).map((ind) => <ImpactoGrafico key={String(ind.id ?? ind.nombre)} nombre={String(ind.nombre ?? "—")} unidad={ind.unidad as string | null | undefined} grafico={ind.grafico as { puntos: Array<{ serie: string; valor: string; numerico: number | null; es_proyeccion: boolean }>; unidad?: string | null } | null | undefined} antes={ind.antes != null ? String(ind.antes) : ind.valor_antes != null ? String(ind.valor_antes) : null} proyectado={ind.proyectado != null ? String(ind.proyectado) : ind.valor_proyectado != null ? String(ind.valor_proyectado) : null} real={ind.real != null ? String(ind.real) : ind.valor_real != null ? String(ind.valor_real) : null} />)}</tbody></table>
          <p className="cc-inline-links"><Link to={`/evaluaciones/${evaluacionId}?tab=informes`}>Informes</Link>{" · "}<Link to={`/resultados-inteligencia?expediente_id=${evaluacionId}`}>Resultados</Link>{" · "}<Link to={`/evaluaciones/${evaluacionId}?tab=valor`}>Valoración</Link></p>
        </details>
      )}
    </div>
  );
}
