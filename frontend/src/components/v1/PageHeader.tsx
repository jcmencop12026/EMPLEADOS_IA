import type { ReactNode } from "react";

type Props = {
  title: string;
  subtitle?: string;
  eyebrow?: string;
  actions?: ReactNode;
  className?: string;
};

export function PageHeader({ title, subtitle, eyebrow, actions, className = "" }: Props) {
  return (
    <header className={`v1-page-header ${className}`.trim()}>
      <div className="v1-page-header__main">
        {eyebrow && <p className="v1-eyebrow">{eyebrow}</p>}
        <h1>{title}</h1>
        {subtitle && <p className="v1-page-header__subtitle">{subtitle}</p>}
      </div>
      {actions && <div className="v1-page-header__actions">{actions}</div>}
    </header>
  );
}
