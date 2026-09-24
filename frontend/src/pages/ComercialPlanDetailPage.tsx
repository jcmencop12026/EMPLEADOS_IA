import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchCommercialPlan, type CommercialPlanItem } from "../api";
import { CredentialModeBadge } from "../components/comercial/CredentialModeBadge";
import { HelpTooltip } from "../components/comercial/HelpTooltip";
import { formatMoney, formatNumber, TOOLTIPS } from "../lib/comercialLabels";
import { usePermissions } from "../hooks/usePermissions";

export function ComercialPlanDetailPage() {
  const { planId } = useParams<{ planId: string }>();
  const { has } = usePermissions();
  const [plan, setPlan] = useState<CommercialPlanItem | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!planId) return;
    fetchCommercialPlan(planId)
      .then(setPlan)
      .catch((e) => setError(e instanceof Error ? e.message : "Error"));
  }, [planId]);

  if (error) return <p className="error-text">{error}</p>;
  if (!plan) return <p>Cargando plan…</p>;

  const limits = plan.limits ?? {};
  const currency = plan.currency ?? "USD";

  return (
    <div className="ops-page">
      <header className="ops-header">
        <Link to="/comercial/segmentacion">← Planes y segmentación</Link>
        <h1>{plan.name}</h1>
        <p className="muted">Código: {plan.code}</p>
        <CredentialModeBadge mode={plan.credential_mode} />
      </header>

      <div className="notice-banner">
        <strong>Sin IA ilimitada.</strong> Todo consumo IA está acotado por tokens y/o presupuesto incluido.
      </div>

      <section className="panel compact-panel">
        <h2>Capacidades incluidas</h2>
        <div className="metrics-grid compact-metrics">
          <div><strong>Empleados IA</strong><span>{formatNumber(limits.empleados_ia as number | undefined)}</span></div>
          <div><strong>Usuarios</strong><span>{formatNumber(limits.usuarios as number | undefined)}</span></div>
          <div><strong>Automatizaciones</strong><span>{formatNumber(limits.automatizaciones as number | undefined)}</span></div>
          <div><strong>Integraciones</strong><span>{formatNumber(limits.integraciones as number | undefined)}</span></div>
          <div><strong>Almacenamiento</strong><span>{limits.almacenamiento_gb ? `${limits.almacenamiento_gb} GB` : "—"}</span></div>
          <div><strong>Soporte / SLA</strong><span>{String(limits.soporte ?? limits.sla ?? "—")}</span></div>
        </div>
      </section>

      <section className="panel compact-panel">
        <h2>
          Consumo IA incluido
          <HelpTooltip text="Cupos definidos en el plan. El sobreconsumo puede generar cargo o bloqueo según configuración." />
        </h2>
        <div className="metrics-grid compact-metrics">
          <div>
            <strong>Tokens incluidos</strong>
            <span>{formatNumber(plan.consumo_ia_incluido_tokens)}</span>
          </div>
          <div>
            <strong>Presupuesto IA incluido</strong>
            <span>{formatMoney(plan.presupuesto_ia_incluido, currency)}</span>
          </div>
          <div>
            <strong>Excedente por millón</strong>
            <span>{plan.excedente_ia_por_millon != null ? formatMoney(plan.excedente_ia_por_millon, currency) : "—"}</span>
          </div>
          <div>
            <strong>Alerta consumo</strong>
            <span>{plan.alerta_consumo_pct != null ? `${plan.alerta_consumo_pct}%` : "—"}</span>
          </div>
          <div>
            <strong>Bloqueo excedente</strong>
            <span>{plan.bloqueo_excedente ? "Sí" : "No"}</span>
            <HelpTooltip text={TOOLTIPS.sobreconsumo} />
          </div>
        </div>
        {has("finops.view") && (
          <p className="muted">
            <Link to="/costos-valor">Ver consumo y costos IA (FinOps) →</Link>
          </p>
        )}
      </section>

      <section className="panel compact-panel">
        <h2>Parámetros comerciales</h2>
        <div className="metrics-grid compact-metrics">
          <div><strong>Precio base mensual</strong><span>{formatMoney(plan.precio_base_mensual, currency)}</span></div>
          <div><strong>Margen mínimo</strong><span>{(plan.margen_minimo_pct * 100).toFixed(0)}%</span></div>
          <div><strong>Fracción valor sugerida</strong><span>{plan.fraccion_valor_sugerida != null ? `${(plan.fraccion_valor_sugerida * 100).toFixed(0)}%` : "—"}</span></div>
          <div><strong>Precio mínimo</strong><span>{formatMoney(plan.precio_minimo, currency)}</span></div>
          <div><strong>Precio máximo</strong><span>{formatMoney(plan.precio_maximo, currency)}</span></div>
        </div>
      </section>

      {plan.descripcion && (
        <section className="panel compact-panel">
          <h2>Descripción</h2>
          <p>{plan.descripcion}</p>
        </section>
      )}
    </div>
  );
}
