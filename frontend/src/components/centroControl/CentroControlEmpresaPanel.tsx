import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  fetchEvaluacion,
  fetchEvaluacionImpacto,
  type EvaluacionExpedienteDetail,
} from "../../api";
import { SiguienteAccionPanel } from "../evaluacion/SiguienteAccionPanel";
import { CadenaAnaliticaPanel } from "../evaluacion/CadenaAnaliticaPanel";
import { CONFIANZA, ESTADO_EXPEDIENTE, label } from "../../lib/evaluacionLabels";

type Props = {
  evaluacionId: string;
};

export function CentroControlEmpresaPanel({ evaluacionId }: Props) {
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

  if (loading && !exp) return <p className="muted">Cargando contexto de empresa…</p>;
  if (error && !exp) return <p className="error">{error}</p>;
  if (!exp) return null;

  const oportunidades = exp.hallazgos.filter((h) => h.opportunity_id).length;
  const indicadores = (impacto?.indicadores as Array<Record<string, unknown>> | undefined) ?? [];

  const entidadesRelacionadas = useMemo(() => {
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

  return (
    <div className="cc-empresa-panel">
      <section className="panel compact-panel cc-empresa-header-panel">
        <div className="cc-empresa-header">
          <div>
            <p className="eyebrow">Puesto de mando — empresa seleccionada</p>
            <h2>{exp.entidad_nombre}</h2>
            <p className="muted">{exp.codigo} · {exp.titulo} · {label(ESTADO_EXPEDIENTE, exp.estado)}</p>
          </div>
          <div className="cc-empresa-actions">
            <Link to={`/evaluaciones/${evaluacionId}`} className="btn primary small">Abrir cabina</Link>
            <Link to={`/presentacion/${evaluacionId}`} className="btn secondary small">Presentación</Link>
            <Link to={`/evaluaciones/${evaluacionId}?tab=vista-empresa`} className="btn secondary small">Ver como empresa</Link>
          </div>
        </div>
        <div className="executive-kpi-strip">
          <div className="executive-kpi"><span>Información</span><strong>{exp.porcentaje_informacion}%</strong></div>
          <div className="executive-kpi"><span>Confianza</span><strong>{label(CONFIANZA, exp.confianza_global)}</strong></div>
          <div className="executive-kpi"><span>Oportunidades</span><strong>{oportunidades}</strong></div>
          <div className="executive-kpi"><span>Valor potencial</span><strong>{exp.valor_potencial ?? "—"}</strong></div>
          <div className="executive-kpi"><span>Hallazgos</span><strong>{exp.hallazgos.length}</strong></div>
          <div className="executive-kpi"><span>Nivel</span><strong>{exp.nivel}</strong></div>
        </div>
      </section>

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

      <div className="cc-grid-2">
        <section className="panel compact-panel">
          <SiguienteAccionPanel
            expedienteId={evaluacionId}
            onRefresh={load}
            onNavigateTab={() => undefined}
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
            <Link to={`/oportunidades`}>Oportunidades</Link>
          </p>
        </section>
      </div>

      {indicadores.length > 0 && (
        <section className="panel compact-panel">
          <h2 className="section-title">Valor — antes / proyectado / real</h2>
          <table className="data-table compact-table">
            <thead>
              <tr><th>Indicador</th><th>Antes</th><th>Proyectado</th><th>Real</th></tr>
            </thead>
            <tbody>
              {indicadores.slice(0, 6).map((ind) => (
                <tr key={String(ind.id ?? ind.nombre)}>
                  <td>{String(ind.nombre ?? "—")}</td>
                  <td>{String(ind.valor_antes ?? "—")}</td>
                  <td>{String(ind.valor_proyectado ?? "—")}</td>
                  <td>{String(ind.valor_real ?? "—")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}
