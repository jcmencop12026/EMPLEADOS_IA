import { Link } from "react-router-dom";
import { ImpactoGrafico } from "./ImpactoGrafico";
import { EmptyState, FormSection } from "../v1";

type Props = {
  expedienteId: string;
  impacto: Record<string, unknown> | null;
};

export function CabinaResultadosPanel({ expedienteId, impacto }: Props) {
  const indicadores = (impacto?.indicadores as Array<Record<string, unknown>>) ?? [];
  const resumen = impacto?.resumen as Record<string, unknown> | undefined;
  const esDemo = Boolean(resumen?.es_demo);

  return (
    <FormSection
      title="Resultados e indicadores"
      description="Tablero Antes → Proyectado → Real. Las proyecciones no se presentan como resultados conseguidos."
    >
      {esDemo && (
        <p className="demo-banner" role="status">
          <strong>DEMO — DATOS SIMULADOS</strong> — use esta vista para entender qué se medirá cuando existan datos reales.
        </p>
      )}

      {indicadores.length === 0 ? (
        <EmptyState
          title="Aún no hay resultados medidos"
          description="Defina indicadores en la pestaña Valor y complete el diagnóstico. EIAAX comparará el estado anterior, la proyección y el valor real cuando existan mediciones."
          action={
            <div className="ops-actions">
              <Link to={`/evaluaciones/${expedienteId}?tab=valor`} className="btn primary">
                Definir indicadores en Valor
              </Link>
              <Link to={`/resultados-inteligencia?expediente_id=${expedienteId}`} className="btn secondary">
                Inteligencia de resultados
              </Link>
            </div>
          }
        />
      ) : (
        <>
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
          <p className="muted small">
            Los indicadores con valor real permiten comparar evolución. Los proyectados permanecen etiquetados como estimación.
          </p>
        </>
      )}

      <p>
        <Link to={`/resultados-inteligencia?expediente_id=${expedienteId}`}>Abrir inteligencia de resultados</Link>
      </p>
    </FormSection>
  );
}
