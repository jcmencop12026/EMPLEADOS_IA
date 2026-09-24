const STEPS = [
  "Oportunidad detectada",
  "Acción definida",
  "Aprobación",
  "Plan de trabajo",
  "Ejecución",
  "Resultado",
  "Materialización",
] as const;

type Props = {
  currentStep: number;
  className?: string;
};

export function OpportunityProgress({ currentStep, className = "" }: Props) {
  const step = Math.max(0, Math.min(currentStep, STEPS.length - 1));
  return (
    <nav className={`v1-opp-progress ${className}`.trim()} aria-label="Progreso de oportunidad">
      <ol className="v1-opp-progress__list">
        {STEPS.map((label, i) => {
          const state = i < step ? "done" : i === step ? "current" : "pending";
          return (
            <li key={label} className={`v1-opp-progress__item v1-opp-progress__item--${state}`}>
              <span className="v1-opp-progress__marker" aria-hidden="true">{i + 1}</span>
              <span className="v1-opp-progress__label">{label}</span>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

export function opportunityStepFromEstado(estado?: string | null): number {
  const map: Record<string, number> = {
    DETECTADA: 0,
    EN_EVALUACION: 1,
    PRIORIZADA: 1,
    PROPUESTA: 2,
    PENDIENTE_APROBACION: 2,
    APROBADA: 3,
    EN_EJECUCION: 4,
    EN_SEGUIMIENTO: 5,
    MATERIALIZADA: 6,
    CERRADA: 6,
    FALLIDA: 4,
    DESCARTADA: 0,
    DATOS_INSUFICIENTES: 0,
  };
  return map[estado ?? ""] ?? 0;
}
