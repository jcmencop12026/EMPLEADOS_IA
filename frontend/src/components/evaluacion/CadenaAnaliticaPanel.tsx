import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { fetchCadenaAnalitica, type CadenaAnaliticaResponse } from "../../api";
import { EmptyState, FormSection } from "../v1";

const PASO_LABELS: Record<string, string> = {
  EVIDENCIA: "Evidencia",
  ANALISIS: "Análisis",
  HALLAZGO: "Hallazgo",
  CAUSA: "Causa",
  IMPACTO: "Impacto",
  OPORTUNIDAD: "Oportunidad",
  RECOMENDACION: "Recomendación",
  ACCION: "Acción",
};

const PASO_ORDER = [
  "EVIDENCIA",
  "ANALISIS",
  "HALLAZGO",
  "CAUSA",
  "IMPACTO",
  "OPORTUNIDAD",
  "RECOMENDACION",
  "ACCION",
];

type Props = {
  expedienteId: string;
  compact?: boolean;
  onSyncRequisitos?: () => void;
  onEvaluar?: () => void;
};

export function CadenaAnaliticaPanel({ expedienteId, compact = false, onSyncRequisitos, onEvaluar }: Props) {
  const [data, setData] = useState<CadenaAnaliticaResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchCadenaAnalitica(expedienteId)
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar cadena"))
      .finally(() => setLoading(false));
  }, [expedienteId]);

  useEffect(() => {
    void load();
  }, [load]);

  const grouped = useMemo(() => {
    const map = new Map<string, CadenaAnaliticaResponse["nodos"]>();
    for (const paso of PASO_ORDER) map.set(paso, []);
    for (const nodo of data?.nodos ?? []) {
      const list = map.get(nodo.paso) ?? [];
      list.push(nodo);
      map.set(nodo.paso, list);
    }
    return PASO_ORDER.map((paso) => ({ paso, nodos: map.get(paso) ?? [] })).filter((g) => g.nodos.length > 0);
  }, [data]);

  if (loading && !data) return <p className="muted small">Cargando cadena analítica…</p>;
  if (error && !data) return <p className="error small">{error}</p>;
  if (!data || data.total === 0) {
    return (
      <FormSection title="Cadena analítica" description="Hallazgo → impacto → oportunidad → recomendación → acción">
        <EmptyState
          title="Cadena analítica pendiente"
          description="Complete información, sincronice requisitos o ejecute la evaluación para que EIAAX construya el flujo de evidencia a acción."
          action={
            <div className="ops-actions">
              {onSyncRequisitos && (
                <button type="button" className="btn secondary small" onClick={onSyncRequisitos}>
                  Sincronizar requisitos
                </button>
              )}
              {onEvaluar && (
                <button type="button" className="btn primary small" onClick={onEvaluar}>
                  Ejecutar evaluación
                </button>
              )}
            </div>
          }
        />
      </FormSection>
    );
  }

  return (
    <FormSection
      title="Cadena analítica"
      description={`${data.total} elemento(s) — flujo de inteligencia del expediente`}
    >
      <div className="cadena-head">
        <button type="button" className="btn small secondary" onClick={load}>Actualizar</button>
      </div>
      <div className={`cadena-analitica-panel cadena-flow${compact ? " compact" : ""}`}>
        {grouped.map(({ paso, nodos }, idx) => (
          <div key={paso} className="cadena-step">
            {idx > 0 && <span className="cadena-arrow" aria-hidden>→</span>}
            <div className="cadena-step-box">
              <span className="cadena-step-label">{PASO_LABELS[paso] ?? paso}</span>
              <ul className="cadena-step-items">
                {nodos.slice(0, compact ? 2 : 5).map((n) => (
                  <li key={`${paso}-${n.id ?? n.titulo}`}>
                    {n.enlace ? (
                      <Link to={n.enlace} title={n.detalle ?? undefined}>{n.titulo}</Link>
                    ) : (
                      <span title={n.detalle ?? undefined}>{n.titulo}</span>
                    )}
                    {n.detalle && !compact && <p className="muted small cadena-detalle">{n.detalle}</p>}
                  </li>
                ))}
                {nodos.length > (compact ? 2 : 5) && (
                  <li className="muted small">+{nodos.length - (compact ? 2 : 5)} más</li>
                )}
              </ul>
            </div>
          </div>
        ))}
      </div>
    </FormSection>
  );
}
