import { Link } from "react-router-dom";
import { label, CONFIANZA } from "../../lib/evaluacionLabels";
import { EmptyState, FormSection, KpiStrip } from "../v1";

type Props = {
  expedienteId: string;
  valorPotencial?: string | number | null;
  porcentajeInformacion: number;
  confianzaGlobal: string;
};

export function CabinaConsumoPanel({
  expedienteId,
  valorPotencial,
  porcentajeInformacion,
  confianzaGlobal,
}: Props) {
  const hasContext = valorPotencial != null || porcentajeInformacion > 0;

  return (
    <FormSection
      title="Consumo de capacidad IA"
      description="Qué se consume, para qué y en qué contexto de este expediente. Los costos consolidados se gestionan a nivel organización."
    >
      <KpiStrip
        items={[
          { id: "valor", label: "Valor potencial expediente", value: valorPotencial ?? "—", tone: "value" },
          { id: "info", label: "Información completada", value: `${porcentajeInformacion}%` },
          { id: "conf", label: "Confianza global", value: label(CONFIANZA, confianzaGlobal) },
        ]}
      />

      {!hasContext ? (
        <EmptyState
          title="Sin datos de consumo vinculados"
          description="El consumo de IA se registra cuando hay empleados activos, ejecuciones o automatizaciones asociadas a este expediente. Active operación o ejecute diagnósticos para generar actividad medible."
          action={
            <div className="ops-actions">
              <Link to={`/evaluaciones/${expedienteId}?tab=operacion`} className="btn primary">
                Ir a Operación
              </Link>
              <Link to="/costos-valor" className="btn secondary">
                Ver costos y valor
              </Link>
            </div>
          }
        />
      ) : (
        <p className="muted small">
          El detalle de tokens, modelos y costos por ejecución aparece en la consola de costos cuando existen consumos
          atribuibles. Mientras tanto, use los indicadores del expediente como contexto de madurez.
        </p>
      )}

      <div className="ops-actions">
        <Link to="/costos-valor" className="btn secondary small">Consola de costos y valor</Link>
        <Link to="/ejecuciones" className="btn secondary small">Ejecuciones</Link>
        <Link to={`/evaluaciones/${expedienteId}?tab=operacion`} className="btn secondary small">Operación del expediente</Link>
      </div>
    </FormSection>
  );
}
