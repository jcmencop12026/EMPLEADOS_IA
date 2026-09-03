import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchFinOpsDashboard, type FinOpsDashboard } from "../../api";
import { ImpactoGrafico } from "./ImpactoGrafico";
import { ImpactoIndicadorForm } from "./ImpactoIndicadorForm";

type Props = {
  expedienteId: string;
  impacto: Record<string, unknown> | null;
  canManageIndicadores: boolean;
  onImpactoRefresh: () => void;
};

function fmt(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "number") return v.toLocaleString("es-CO");
  return String(v);
}

export function CabinaValorPanel({ expedienteId, impacto, canManageIndicadores, onImpactoRefresh }: Props) {
  const [finops, setFinops] = useState<FinOpsDashboard | null>(null);

  useEffect(() => {
    fetchFinOpsDashboard().then(setFinops).catch(() => undefined);
  }, [expedienteId]);

  const indicadores = (impacto?.indicadores as Array<Record<string, unknown>> | undefined) ?? [];
  const resumen = impacto?.resumen as Record<string, unknown> | undefined;
  const interpretacion = impacto?.interpretacion as Record<string, unknown> | undefined;
  const esDemo = Boolean(resumen?.es_demo);

  const demoAmount = (key: string) => {
    const block = resumen?.[key] as { monto?: number; etiqueta?: string } | undefined;
    if (!block?.monto) return "—";
    return `${block.etiqueta ?? key}: $${Number(block.monto).toLocaleString("es-CO")} COP`;
  };

  return (
    <div className="cabina-valor-panel">
      <section className="panel compact-panel">
        <h2>Valor económico ejecutivo</h2>
        {esDemo && (
          <p className="demo-banner" role="status">
            <strong>DEMO — DATOS SIMULADOS</strong> — ninguna cifra equivale a verificación real.
          </p>
        )}
        <p className="muted small potential-excluded">
          El valor potencial no se suma al valor realizado. Precio sugerido y margen son información privada.
        </p>
        <div className="value-nature-grid compact">
          {esDemo ? (
            <>
              <div className="value-nature-card estimated">
                <span className="value-nature-head">Simulación verificado</span>
                <span className="value-nature-amount">{demoAmount("simulacion_verificado")}</span>
              </div>
              <div className="value-nature-card estimated">
                <span className="value-nature-head">Estimado</span>
                <span className="value-nature-amount">{demoAmount("estimado")}</span>
              </div>
              <div className="value-nature-card potential">
                <span className="value-nature-head">Potencial</span>
                <span className="value-nature-amount">{demoAmount("potencial")}</span>
              </div>
            </>
          ) : (
            <>
              <div className="value-nature-card verified">
                <span className="value-nature-head">Verificado</span>
                <span className="value-nature-amount">{fmt(resumen?.verificado)}</span>
              </div>
              <div className="value-nature-card estimated">
                <span className="value-nature-head">Estimado</span>
                <span className="value-nature-amount">{fmt(resumen?.estimado)}</span>
              </div>
              <div className="value-nature-card potential">
                <span className="value-nature-head">Potencial</span>
                <span className="value-nature-amount">{fmt(resumen?.potencial)}</span>
              </div>
            </>
          )}
          <div className="value-nature-card price-base">
            <span className="value-nature-head">Realizado</span>
            <span className="value-nature-amount">{fmt(resumen?.realizado ?? finops?.total_value)}</span>
          </div>
        </div>
        <dl className="detail-grid compact">
          <dt>Consumo IA periodo</dt><dd>{finops?.total_cost_label ?? "—"}</dd>
          <dt>Valor generado</dt><dd>{finops?.total_value_label ?? "—"}</dd>
          <dt>ROI</dt><dd>{finops?.roi_label ?? "—"}</dd>
          <dt>Ahorro estimado</dt><dd>{finops?.estimated_savings ?? "—"}</dd>
        </dl>
        {interpretacion && (
          <dl className="detail-grid compact cc-interpretacion">
            <dt>Qué significa</dt><dd>{String(interpretacion.que_significa ?? "—")}</dd>
            <dt>Requiere atención</dt><dd>{String(interpretacion.requiere_atencion ?? "—")}</dd>
            <dt>Recomendación EIAAX</dt><dd>{String(interpretacion.recomendacion ?? "—")}</dd>
          </dl>
        )}
        <p><Link to="/costos-valor">Consola FinOps completa</Link></p>
      </section>

      <section className="panel compact-panel">
        <h2>Indicadores Antes / Proyectado / Real</h2>
        {canManageIndicadores && (
          <ImpactoIndicadorForm expedienteId={expedienteId} onCreated={onImpactoRefresh} />
        )}
        {indicadores.length === 0 ? (
          <p className="muted">
            Sin indicadores registrados. Complete información y diagnóstico; EIAAX puede proponer indicadores desde hallazgos.
          </p>
        ) : (
          <table className="data-table compact-table impacto-indicadores-table">
            <thead>
              <tr><th>Indicador</th><th>Antes</th><th>Proyectado</th><th>Real</th><th>Evolución</th></tr>
            </thead>
            <tbody>
              {indicadores.map((ind) => (
                <ImpactoGrafico
                  key={String(ind.id ?? ind.nombre)}
                  nombre={String(ind.nombre ?? "—")}
                  unidad={ind.unidad as string | null | undefined}
                  grafico={ind.grafico as { puntos: Array<{ serie: string; valor: string; numerico: number | null; es_proyeccion: boolean }>; unidad?: string | null } | null | undefined}
                  antes={ind.antes != null ? String(ind.antes) : null}
                  proyectado={ind.proyectado != null ? String(ind.proyectado) : null}
                  real={ind.real != null ? String(ind.real) : null}
                />
              ))}
            </tbody>
          </table>
        )}
        <p className="muted small">
          <Link to={`/resultados-inteligencia?expediente_id=${expedienteId}`}>Tablero completo de resultados</Link>
        </p>
      </section>
    </div>
  );
}
