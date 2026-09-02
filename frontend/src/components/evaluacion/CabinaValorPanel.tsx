import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchFinOpsDashboard, type FinOpsDashboard } from "../../api";
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

  return (
    <div className="cabina-valor-panel">
      <section className="panel compact-panel">
        <h2>Valor económico ejecutivo</h2>
        <p className="muted small potential-excluded">
          El valor potencial no se suma al valor realizado. Precio sugerido y margen son información privada.
        </p>
        <div className="value-nature-grid compact">
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
          <table className="data-table compact-table">
            <thead>
              <tr><th>Indicador</th><th>Antes</th><th>Proyectado</th><th>Real</th></tr>
            </thead>
            <tbody>
              {indicadores.map((ind) => (
                <tr key={String(ind.id ?? ind.nombre)}>
                  <td>{String(ind.nombre ?? "—")}</td>
                  <td>{String(ind.antes ?? "—")}</td>
                  <td>{String(ind.proyectado ?? "—")}</td>
                  <td>{String(ind.real ?? "—")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
