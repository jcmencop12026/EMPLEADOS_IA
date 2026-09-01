import type { OptimizacionRecomendacion } from "../../api";
import { HelpTooltip } from "./HelpTooltip";
import { EstadoBadge } from "./EstadoBadge";
import { TOOLTIPS } from "../../lib/optimizacionLabels";

type Props = { detail: OptimizacionRecomendacion };

export function ExecutionStatusPanel({ detail }: Props) {
  const ej = detail.ejecucion;
  if (!ej && detail.estado !== "APROBADA" && detail.estado !== "PROPUESTA") {
    return null;
  }

  const ejEstado = ej?.estado;
  const mostrarEjecutada = detail.estado === "EJECUTADA" && ejEstado !== "FALLIDA";
  const mostrarFallida = detail.estado === "FALLIDA" || ejEstado === "FALLIDA";

  return (
    <section className="card compact-panel" style={{ marginBottom: "1rem" }}>
      <h2>
        Ejecución
        <HelpTooltip text={TOOLTIPS.ejecucion_automatica} />
      </h2>
      <div className="compact-metrics">
        <div>
          <span className="muted">Estado recomendación</span>
          <EstadoBadge estado={detail.estado} />
        </div>
        {ejEstado && (
          <div>
            <span className="muted">Estado ejecución</span>
            <EstadoBadge estado={ejEstado} tipo="ejecucion" />
          </div>
        )}
        <div>
          <span className="muted">Tipo</span>
          <strong>{ej?.tipo ?? "—"}</strong>
        </div>
        <div>
          <span className="muted">
            ID de correlación
            <HelpTooltip text={TOOLTIPS.correlation_id} />
          </span>
          <span className="mono">{ej?.correlation_id?.slice(0, 12) ?? "—"}</span>
        </div>
        <div>
          <span className="muted">Ejecutada</span>
          <strong>{ej?.executed_at ? new Date(String(ej.executed_at)).toLocaleString("es-CO") : "—"}</strong>
        </div>
        <div>
          <span className="muted">Referencia externa</span>
          <strong>{ej?.referencia_externa ?? ej?.execution_reference ?? "—"}</strong>
        </div>
      </div>

      {ejEstado === "PENDIENTE_EJECUCION_HUMANA" && (
        <p className="notice-banner subtle">
          Requiere confirmación humana externa antes de marcar como ejecutada.
          <HelpTooltip text={TOOLTIPS.ejecucion_humana} />
        </p>
      )}

      {mostrarFallida && (
        <p className="alert alert-error">
          Ejecución fallida: {String((ej?.error as { message?: string })?.message ?? ej?.error ?? "Error desconocido")}
        </p>
      )}

      {mostrarEjecutada && !mostrarFallida && (
        <p className="notice-banner">Recomendación ejecutada correctamente.</p>
      )}

      {(ej?.learning_refs?.length ?? 0) > 0 && (
        <details className="compact-details" style={{ marginTop: 8 }}>
          <summary>Referencias de aprendizaje ({ej!.learning_refs!.length})</summary>
          <pre className="compact-pre">{JSON.stringify(ej!.learning_refs, null, 2)}</pre>
        </details>
      )}

      {(ej?.oportunidades?.length ?? 0) > 0 && (
        <details className="compact-details" style={{ marginTop: 8 }}>
          <summary>Oportunidades asociadas</summary>
          <ul>
            {(ej!.oportunidades as Array<{ opportunity_id?: string }>).map((o, i) => (
              <li key={i} className="mono">{o.opportunity_id?.slice(0, 12) ?? "—"}</li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}
