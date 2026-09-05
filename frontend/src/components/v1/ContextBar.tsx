import type { ReactNode } from "react";

type Row = {
  label: string;
  value: ReactNode;
  hint?: string;
  emphasis?: boolean;
};

type Props = {
  sessionLabel: string;
  sessionValue: ReactNode;
  analysisLabel: string;
  analysisValue: ReactNode;
  extra?: Row[];
  className?: string;
};

export function ContextBar({
  sessionLabel,
  sessionValue,
  analysisLabel,
  analysisValue,
  extra = [],
  className = "",
}: Props) {
  return (
    <div className={`v1-context-bar ${className}`.trim()} role="region" aria-label="Contexto de sesión y análisis">
      <div className="v1-context-bar__block v1-context-bar__session">
        <span className="v1-context-bar__label">{sessionLabel}</span>
        <span className="v1-context-bar__value">{sessionValue}</span>
      </div>
      <div className="v1-context-bar__divider" aria-hidden="true" />
      <div className="v1-context-bar__block v1-context-bar__analysis">
        <span className="v1-context-bar__label">{analysisLabel}</span>
        <span className="v1-context-bar__value v1-context-bar__value--emphasis">{analysisValue}</span>
      </div>
      {extra.map((row) => (
        <div key={row.label} className={`v1-context-bar__block ${row.emphasis ? "v1-context-bar__block--emphasis" : ""}`}>
          <span className="v1-context-bar__label">{row.label}</span>
          <span className="v1-context-bar__value">{row.value}</span>
          {row.hint && <span className="v1-context-bar__hint">{row.hint}</span>}
        </div>
      ))}
    </div>
  );
}
