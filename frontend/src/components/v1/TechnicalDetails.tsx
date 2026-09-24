import type { ReactNode } from "react";

type Props = {
  title?: string;
  children: ReactNode;
  defaultOpen?: boolean;
  className?: string;
};

export function TechnicalDetails({ title = "Detalle técnico", children, defaultOpen = false, className = "" }: Props) {
  return (
    <details className={`v1-technical-details ${className}`.trim()} open={defaultOpen}>
      <summary>{title}</summary>
      <div className="v1-technical-details__body">{children}</div>
    </details>
  );
}
