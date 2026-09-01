import { IMPL_CYCLE_STEPS } from "../../lib/comercialLabels";

const STATE_MAP: Record<string, number> = {
  PLANIFICACION: 0,
  PREPARACION: 1,
  EN_IMPLEMENTACION: 2,
  PILOTO: 2,
  EN_PRODUCCION: 3,
  OPERACION: 5,
  CERRADO: 6,
};

type Props = { estado?: string };

export function ImplementationCycleBar({ estado }: Props) {
  const idx = STATE_MAP[estado ?? ""] ?? 0;
  return (
    <div className="impl-cycle-bar" role="list" aria-label="Ciclo de implementación">
      {IMPL_CYCLE_STEPS.map((step, i) => (
        <div
          key={step.key}
          role="listitem"
          className={`impl-cycle-step ${i <= idx ? "done" : ""} ${i === idx ? "current" : ""}`}
          title={step.label}
        >
          <span className="impl-cycle-dot" />
          <span className="impl-cycle-label">{step.label}</span>
        </div>
      ))}
    </div>
  );
}
