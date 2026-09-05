import { useEffect, useState } from "react";
import { fetchSiguienteAccion } from "../../api";
import { ErrorState, LoadingState } from "../AsyncState";
import { INTENCION_AGENTE, label, labelEstadoCapacidad } from "../../lib/evaluacionLabels";
import { labelCabinaTab } from "../../lib/siguienteAccionTabMap";
import { EmptyState, NextActionHero, StatusBadge } from "../v1";

type AccionSugerida = {
  codigo: string;
  titulo: string;
  descripcion: string;
  prioridad?: number;
  intencion?: string;
  pestaña?: string;
  disponible?: boolean;
  estado_es?: string;
};

type Props = {
  expedienteId: string;
  onNavigateTab?: (tab: string) => void;
  onRefresh?: () => void;
};

export function SiguienteAccionPanel({ expedienteId, onNavigateTab, onRefresh }: Props) {
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    fetchSiguienteAccion(expedienteId)
      .then((r) => { setData(r); setError(null); })
      .catch((e) => setError(e instanceof Error ? e.message : "Error"))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [expedienteId]);

  if (loading) return <LoadingState message="Determinando siguiente acción…" />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!data) {
    return (
      <EmptyState
        title="Sin sugerencias disponibles"
        description="Complete información del expediente o ejecute la evaluación para que EIAAX proponga la siguiente acción."
        action={
          <button type="button" className="btn secondary small" onClick={() => { load(); onRefresh?.(); }}>
            Actualizar
          </button>
        }
      />
    );
  }

  const principal = data.principal as AccionSugerida;
  const alternativas = (data.alternativas as AccionSugerida[]) ?? [];

  const meta = (
    <>
      {principal.intencion && (
        <StatusBadge tone="info" label={label(INTENCION_AGENTE, principal.intencion)} />
      )}
      {principal.estado_es && (
        <StatusBadge
          tone={principal.disponible === false ? "warning" : "neutral"}
          label={labelEstadoCapacidad(principal.estado_es)}
        />
      )}
    </>
  );

  return (
    <section className="siguiente-accion-panel">
      <NextActionHero
        title={principal.titulo}
        description={principal.descripcion}
        actionLabel={principal.pestaña && principal.disponible !== false ? `Ir a ${labelCabinaTab(principal.pestaña)}` : undefined}
        onAction={principal.pestaña && onNavigateTab && principal.disponible !== false ? () => onNavigateTab(principal.pestaña!) : undefined}
        meta={meta}
      />
      <div className="siguiente-accion-toolbar">
        <button type="button" className="btn small secondary" onClick={() => { load(); onRefresh?.(); }}>
          Actualizar recomendación
        </button>
      </div>
      {alternativas.length > 0 && (
        <div className="siguiente-accion-alternativas">
          <p className="muted small">Otras acciones posibles</p>
          <ul className="compact-list">
            {alternativas.map((a) => (
              <li key={a.codigo}>
                <StatusBadge
                  tone="neutral"
                  className="tiny"
                  label={a.intencion ? label(INTENCION_AGENTE, a.intencion) : "Acción"}
                />
                {a.titulo}
                {a.pestaña && onNavigateTab && (
                  <button type="button" className="btn-link" onClick={() => onNavigateTab(a.pestaña!)}>
                    Ver
                  </button>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
