import type { ReactNode } from "react";

type Props = {
  title: string;
  subtitle?: string;
  children: ReactNode;
  actions?: ReactNode;
  demo?: boolean;
  className?: string;
};

export function ExecutiveCard({ title, subtitle, children, actions, demo, className = "" }: Props) {
  return (
    <article className={`v1-executive-card ${demo ? "v1-executive-card--demo" : ""} ${className}`.trim()}>
      <header className="v1-executive-card__head">
        <div>
          <h3>{title}</h3>
          {subtitle && <p>{subtitle}</p>}
        </div>
        {actions && <div className="v1-executive-card__actions">{actions}</div>}
      </header>
      <div className="v1-executive-card__body">{children}</div>
    </article>
  );
}
