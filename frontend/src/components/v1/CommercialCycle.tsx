import { StatusBadge } from "./StatusBadge";

const STAGES = [
  { id: "prospecto", label: "Prospecto" },
  { id: "evaluacion", label: "Evaluación" },
  { id: "oportunidad", label: "Oportunidad" },
  { id: "propuesta", label: "Propuesta" },
  { id: "contrato", label: "Contrato" },
  { id: "cliente", label: "Cliente" },
  { id: "operacion", label: "Operación" },
] as const;

type Props = {
  currentStage: string;
  nextStep?: string;
  className?: string;
};

export function CommercialCycle({ currentStage, nextStep, className = "" }: Props) {
  const idx = STAGES.findIndex((s) => s.id === currentStage);
  const current = idx >= 0 ? idx : 0;
  return (
    <div className={`v1-commercial-cycle ${className}`.trim()} aria-label="Ciclo comercial">
      <div className="v1-commercial-cycle__track">
        {STAGES.map((stage, i) => {
          const state = i < current ? "done" : i === current ? "current" : "pending";
          return (
            <div key={stage.id} className={`v1-commercial-cycle__step v1-commercial-cycle__step--${state}`}>
              <span className="v1-commercial-cycle__dot" />
              <span className="v1-commercial-cycle__label">{stage.label}</span>
            </div>
          );
        })}
      </div>
      {nextStep && (
        <p className="v1-commercial-cycle__next">
          <StatusBadge label={`Siguiente: ${nextStep}`} tone="info" />
        </p>
      )}
    </div>
  );
}
