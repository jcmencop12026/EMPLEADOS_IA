import { Link } from "react-router-dom";
import { CICLO_ETAPAS, type CicloChipState, cicloChipState, cicloEtapaRuta } from "../../lib/cicloOperativo";

type Props = {
  currentIndex: number;
  expedienteId?: string;
  isDemo?: boolean;
  compact?: boolean;
  className?: string;
};

export function CycleStepper({ currentIndex, expedienteId, isDemo, compact = false, className = "" }: Props) {
  return (
    <nav
      className={`v1-cycle-stepper v1-cycle-stepper--wrap ${compact ? "v1-cycle-stepper--compact" : ""} ${className}`.trim()}
      aria-label="Ciclo operativo EIAAX"
    >
      <div className="v1-cycle-stepper__track">
        {CICLO_ETAPAS.map((etapa, idx) => {
          const state: CicloChipState = currentIndex >= 0 ? cicloChipState(idx, currentIndex) : "pending";
          return (
            <Link
              key={etapa}
              to={cicloEtapaRuta(etapa, { expedienteId, isDemo })}
              className={`v1-cycle-step v1-cycle-step--${state}`}
              title={`Etapa ${idx + 1}: ${etapa}`}
              aria-current={state === "current" ? "step" : undefined}
            >
              <span className="v1-cycle-step__num">{idx + 1}</span>
              <span className="v1-cycle-step__label">{etapa}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
