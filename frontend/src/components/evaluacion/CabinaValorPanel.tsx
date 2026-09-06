import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchFinOpsDashboard, type FinOpsDashboard } from "../../api";
import { ImpactoGrafico } from "./ImpactoGrafico";
import { ImpactoIndicadorForm } from "./ImpactoIndicadorForm";
import { EmptyState, FormSection, KpiStrip } from "../v1";

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
      <FormSection title="Valor económico ejecutivo" description="Potencial, verificado, estimado y realizado — sin sumar potencial al realizado.">
        {esDemo && (
          <p className="demo-banner" role="status">
            <strong>DEMO — DATOS SIMULADOS</strong> — ninguna cifra equivale a verificación real.
          </p>
        )}
        <p className="muted small potential-excluded">
          El valor potencial no se suma al valor realizado. Precio sugerido y margen son información privada.
        </p>
        <KpiStrip
          items={esDemo
            ? [
                { id: "sim", label: "Simulación verificado", value: demoAmount("simulacion_verificado"), tone: "value" },
                { id: "est", label: "Estimado", value: demoAmount("estimado"), tone: "value" },
                { id: "pot", label: "Potencial", value: demoAmount("potencial"), tone: "value" },
                { id: "real", label: "Realizado", value: fmt(resumen?.realizado ?? finops?.total_value) },
              ]
            : [
                { id: "ver", label: "Verificado", value: fmt(resumen?.verificado), tone: "success" },
                { id: "est", label: "Estimado", value: fmt(resumen?.estimado), tone: "value" },
                { id: "pot", label: "Potencial", value: fmt(resumen?.potencial), tone: "value" },
                { id: "real", label: "Realizado", value: fmt(resumen?.realizado ?? finops?.total_value) },
              ]}
        />
        <dl className="detail-grid compact">
          <dt>Consumo IA periodo</dt><dd>{finops?.total_cost_label ?? "—"}</dd>
          <dt>Valor generado</dt><dd>{finops?.total_value_label ?? "—"}</dd>
          <dt>ROI</dt><dd>{finops?.roi_label ?? "—"}</dd>
          <dt>Ahorro estimado</dt><dd>{finops?.estimated_savings ?? "—"}</dd>
        </dl>
        {finops && (
          <p className="muted small" role="note">
            Costos y consumo consolidados a nivel organización
            {finops.atribucion_nivel ? " (atribución organizacional)" : ""}, no atribuidos exclusivamente a este expediente.
          </p>
        )}
        {interpretacion && (
          <dl className="detail-grid compact cc-interpretacion">
            <dt>Qué significa</dt><dd>{String(interpretacion.que_significa ?? "—")}</dd>
            <dt>Requiere atención</dt><dd>{String(interpretacion.requiere_atencion ?? "—")}</dd>
            <dt>Recomendación EIAAX</dt><dd>{String(interpretacion.recomendacion ?? "—")}</dd>
          </dl>
        )}
        <p><Link to="/costos-valor">Consola de costos y valor</Link></p>
      </FormSection>

      <FormSection title="Indicadores Antes / Proyectado / Real" description="Evolución medible del valor generado">
        {canManageIndicadores && (
          <ImpactoIndicadorForm expedienteId={expedienteId} onCreated={onImpactoRefresh} />
        )}
        {indicadores.length === 0 ? (
          <EmptyState
            title="Sin indicadores registrados"
            description="Complete información y diagnóstico; EIAAX puede proponer indicadores desde hallazgos para medir antes, proyectado y real."
            action={
              canManageIndicadores ? undefined : (
                <Link to={`/evaluaciones/${expedienteId}?tab=diagnostico`} className="btn secondary small">
                  Ir a Diagnóstico
                </Link>
              )
            }
          />
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
      </FormSection>
    </div>
  );
}
