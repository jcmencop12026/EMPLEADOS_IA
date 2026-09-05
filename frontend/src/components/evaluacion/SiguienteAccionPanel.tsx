import { useEffect, useState } from "react";
import { fetchSiguienteAccion } from "../../api";
import { EmptyState, ErrorState, LoadingState } from "../AsyncState";
import { INTENCION_AGENTE, label } from "../../lib/evaluacionLabels";
import { labelCabinaTab } from "../../lib/siguienteAccionTabMap";

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
  if (!data) return <EmptyState title="Sin sugerencias" />;

  const principal = data.principal as AccionSugerida;
  const alternativas = (data.alternativas as AccionSugerida[]) ?? [];

  return (
    <section className="siguiente-accion-panel card">
      <header className="siguiente-accion-header">
        <h3>Siguiente acción sugerida</h3>
        <button type="button" className="btn small" onClick={() => { load(); onRefresh?.(); }}>
          Actualizar
        </button>
      </header>
      <div className={`siguiente-accion-principal ${principal.disponible === false ? "disabled" : ""}`}>
        {principal.intencion && (
          <span className="intencion-badge" title={label(INTENCION_AGENTE, principal.intencion)}>
            {label(INTENCION_AGENTE, principal.intencion)}
          </span>
        )}
        <strong>{principal.titulo}</strong>
        <p className="muted small">{principal.descripcion}</p>
        {principal.pestaña && onNavigateTab && (
          <button
            type="button"
            className="btn small primary"
            disabled={principal.disponible === false}
            onClick={() => onNavigateTab(principal.pestaña!)}
          >
            Ir a {labelCabinaTab(principal.pestaña!)}
          </button>
        )}
        {principal.estado_es && (
          <span className="estado-capacidad-badge">{principal.estado_es}</span>
        )}
      </div>
      {alternativas.length > 0 && (
        <div className="siguiente-accion-alternativas">
          <p className="muted small">Otras acciones posibles</p>
          <ul className="compact-list">
            {alternativas.map((a) => (
              <li key={a.codigo}>
                <span className="intencion-badge tiny">
                  {a.intencion ? label(INTENCION_AGENTE, a.intencion) : "—"}
                </span>
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
