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
import { ImpactoGrafico } from "../evaluacion/ImpactoGrafico";
import { CONFIANZA, ESTADO_EXPEDIENTE, label, labelNivelEvaluacion } from "../../lib/evaluacionLabels";
import { cabinaTabPath, mapSiguienteAccionToCabinaTab } from "../../lib/siguienteAccionTabMap";
import { narrativaCampo } from "../../lib/informeNarrativa";

type Props = {
  evaluacionId: string;
};

export function CentroControlEmpresaPanel({ evaluacionId }: Props) {
  const navigate = useNavigate();
  const [exp, setExp] = useState<EvaluacionExpedienteDetail | null>(null);
  const [impacto, setImpacto] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([
      fetchEvaluacion(evaluacionId),
      fetchEvaluacionImpacto(evaluacionId).catch(() => null),
    ])
      .then(([detail, imp]) => {
        setExp(detail);
        setImpacto(imp);
        setError(null);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar expediente"))
      .finally(() => setLoading(false));
  }, [evaluacionId]);

  useEffect(() => { load(); }, [load]);

  const entidadesRelacionadas = useMemo(() => {
    if (!exp) return [];
    const items: Array<{ nombre: string; tipo: string; enlace: string }> = [];
    const sector = String((exp as Record<string, unknown>).sector ?? "").toLowerCase();
    if (sector.includes("salud")) {
      items.push({
        nombre: exp.entidad_nombre,
        tipo: "IPS / entidad salud",
        enlace: `/evaluaciones/${evaluacionId}?tab=diagnostico`,
      });
    }
    for (const info of exp.informacion ?? []) {
      const pregunta = String(info.etiqueta ?? info.campo ?? "").toLowerCase();
      const respuesta = String(info.respuesta ?? "").trim();
      if (!respuesta) continue;
      if (pregunta.includes("ips") || pregunta.includes("unidad") || pregunta.includes("sede") || pregunta.includes("entidad")) {
        items.push({
          nombre: respuesta,
          tipo: pregunta.includes("ips") ? "IPS" : "Unidad / proceso",
          enlace: `/evaluaciones/${evaluacionId}?tab=diagnostico`,
        });
      }
    }
    const seen = new Set<string>();
    return items.filter((e) => {
      const key = `${e.nombre}-${e.tipo}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }, [exp, evaluacionId]);

  if (loading && !exp) return <p className="muted">Cargando contexto de empresa…</p>;
  if (error && !exp) return <p className="error">{error}</p>;
  if (!exp) return null;

  const oportunidades = exp.hallazgos.filter((h) => h.opportunity_id).length;
  const indicadores = (impacto?.indicadores as Array<Record<string, unknown>> | undefined) ?? [];

  return (
    <div className="cc-empresa-panel">
      <ExecutiveCard
        title={exp.entidad_nombre}
        subtitle={`${exp.codigo} · ${exp.titulo}`}
        demo={exp.entidad_nombre?.startsWith("[DEMO]")}
        actions={<Link to={`/evaluaciones/${evaluacionId}`} className="btn primary small">Abrir cabina</Link>}
      >
        <div className="v1-empresa-meta">
          <StatusBadge label={label(ESTADO_EXPEDIENTE, exp.estado)} tone="info" />
          <span className="muted small">Puesto de mando — empresa seleccionada</span>
        </div>
        <KpiStrip
          className="v1-empresa-kpis"
          items={[
            { id: "info", label: "Información completada", value: `${exp.porcentaje_informacion}%` },
            { id: "conf", label: "Confianza", value: label(CONFIANZA, exp.confianza_global) },
            { id: "opp", label: "Oportunidades", value: oportunidades },
            { id: "hall", label: "Hallazgos", value: exp.hallazgos.length },
            {
              id: "valor",
              label: "Valor potencial",
              value: exp.valor_potencial ?? "—",
              tone: exp.entidad_nombre?.startsWith("[DEMO]") ? undefined : "value",
            },
            { id: "nivel", label: "Nivel", value: labelNivelEvaluacion(exp.nivel) },
          ]}
        />
      </ExecutiveCard>

      {entidadesRelacionadas.length > 0 && (
        <section className="panel compact-panel cc-entidades-relacionadas">
          <h2 className="section-title">Entidades relacionadas</h2>
          <p className="muted small">
            Seleccione una unidad, IPS o proceso para operar en contexto sin abandonar el Centro de Control.
          </p>
          <ul className="cc-entidades-list">
            {entidadesRelacionadas.map((ent) => (
              <li key={`${ent.tipo}-${ent.nombre}`}>
                <Link to={ent.enlace} className="cc-entidad-link">
                  <strong>{ent.nombre}</strong>
                  <span className="muted small">{ent.tipo}</span>
                </Link>
                <span className="cc-entidad-actions">
                  <Link to={ent.enlace} className="btn small secondary">Información</Link>
                  <Link to={`/evaluaciones/${evaluacionId}?tab=diagnostico`} className="btn small secondary">Diagnóstico</Link>
                  <Link to="/directorio" className="btn small secondary">Empleados</Link>
                  <Link to="/operaciones" className="btn small secondary">Operaciones</Link>
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="panel compact-panel">
        <CadenaAnaliticaPanel expedienteId={evaluacionId} compact />
      </section>

      {indicadores.length > 0 && (
        <section className="panel compact-panel cc-tablero-empresa">
          <div className="cc-tablero-head">
            <h2 className="section-title">Tablero empresarial — indicadores</h2>
            <Link to={`/evaluaciones/${evaluacionId}?tab=resultados`} className="btn small secondary">Profundizar</Link>
          </div>
          {exp.entidad_nombre?.startsWith("[DEMO]") && (
            <p className="demo-banner" role="status">DEMO — DATOS SIMULADOS — proyecciones no equivalen a verificación real.</p>
          )}
          <dl className="detail-grid compact cc-interpretacion-strip">
            <dt>Qué ocurrió</dt><dd>{narrativaCampo((impacto?.interpretacion as Record<string, unknown> | undefined)?.que_ocurrio)}</dd>
            <dt>Por qué</dt><dd>{narrativaCampo((impacto?.interpretacion as Record<string, unknown> | undefined)?.por_que)}</dd>
            <dt>Requiere atención</dt><dd>{narrativaCampo((impacto?.interpretacion as Record<string, unknown> | undefined)?.requiere_atencion)}</dd>
            <dt>Oportunidad</dt><dd>{narrativaCampo((impacto?.interpretacion as Record<string, unknown> | undefined)?.oportunidad)}</dd>
            <dt>Recomendación EIAAX</dt><dd>{narrativaCampo((impacto?.interpretacion as Record<string, unknown> | undefined)?.recomendacion)}</dd>
          </dl>
          <p className="muted small">
            Qué ocurrió → por qué importa → qué requiere atención. Proyectado nunca se presenta como real.
          </p>
          <table className="data-table compact-table impacto-indicadores-table">
            <thead>
              <tr><th>Indicador</th><th>Antes</th><th>Proyectado</th><th>Real</th><th>Evolución</th></tr>
            </thead>
            <tbody>
              {indicadores.slice(0, 6).map((ind) => (
                <ImpactoGrafico
                  key={String(ind.id ?? ind.nombre)}
                  nombre={String(ind.nombre ?? "—")}
                  unidad={ind.unidad as string | null | undefined}
                  grafico={ind.grafico as { puntos: Array<{ serie: string; valor: string; numerico: number | null; es_proyeccion: boolean }>; unidad?: string | null } | null | undefined}
                  antes={ind.antes != null ? String(ind.antes) : ind.valor_antes != null ? String(ind.valor_antes) : null}
                  proyectado={ind.proyectado != null ? String(ind.proyectado) : ind.valor_proyectado != null ? String(ind.valor_proyectado) : null}
                  real={ind.real != null ? String(ind.real) : ind.valor_real != null ? String(ind.valor_real) : null}
                />
              ))}
            </tbody>
          </table>
          <p className="cc-inline-links">
            <Link to={`/evaluaciones/${evaluacionId}?tab=informes`}>Informes</Link>
            {" · "}
            <Link to={`/resultados-inteligencia?expediente_id=${evaluacionId}`}>Resultados</Link>
            {" · "}
            <Link to={`/evaluaciones/${evaluacionId}?tab=valor`}>Valoración</Link>
          </p>
        </section>
      )}

      <div className="cc-grid-2">
        <section className="panel compact-panel">
          <SiguienteAccionPanel
            expedienteId={evaluacionId}
            onRefresh={load}
            onNavigateTab={(p) => {
              const tab = mapSiguienteAccionToCabinaTab(p);
              if (tab) navigate(cabinaTabPath(evaluacionId, tab));
            }}
          />
        </section>
        <section className="panel compact-panel">
          <h2 className="section-title">Resumen ejecutivo</h2>
          <dl className="detail-grid compact">
            <dt>Problema</dt><dd>{exp.necesidad ?? "—"}</dd>
            <dt>Objetivo</dt><dd>{exp.objetivo ?? "—"}</dd>
            <dt>Área / proceso</dt><dd>{exp.area_proceso ?? "—"}</dd>
          </dl>
          <p className="muted small">
            El diagnóstico, la solución IA y la operación se gestionan desde la cabina sin duplicar entidades.
          </p>
          <p>
            <Link to={`/evaluaciones/${evaluacionId}`}>Ir a cabina completa</Link>
            {" · "}
            <Link to={`/evaluaciones/${evaluacionId}?tab=resultados`}>Oportunidades y resultados</Link>
          </p>
        </section>
      </div>
    </div>
  );
}
