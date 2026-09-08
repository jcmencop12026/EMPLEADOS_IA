import type { ReactNode } from "react";
import { Link } from "react-router-dom";

type Props = {
  title: string;
  description?: string;
  actionLabel?: string;
  actionHref?: string;
  onAction?: () => void;
  meta?: ReactNode;
  className?: string;
};

export function NextActionHero({
  title,
  description,
  actionLabel,
  actionHref,
  onAction,
  meta,
  className = "",
}: Props) {
  return (
    <section className={`v1-next-action ${className}`.trim()} aria-label="Siguiente acción recomendada">
      <div className="v1-next-action__content">
        <p className="v1-eyebrow">Siguiente acción EIAAX</p>
        <h3 className="v1-next-action__title">{title}</h3>
        {description && <p className="v1-next-action__desc">{description}</p>}
        {meta && <div className="v1-next-action__meta">{meta}</div>}
      </div>
      {(actionHref || onAction) && actionLabel && (
        <div className="v1-next-action__cta">
          {actionHref ? (
            <Link to={actionHref} className="btn primary v1-btn-hero">{actionLabel}</Link>
          ) : (
            <button type="button" className="btn primary v1-btn-hero" onClick={onAction}>{actionLabel}</button>
          )}
        </div>
      )}
    </section>
  );
}
