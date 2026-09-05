import type { ReactNode } from "react";
import { Link } from "react-router-dom";

export type KpiItem = {
  id: string;
  label: string;
  value: ReactNode;
  hint?: string;
  tone?: "default" | "attention" | "success" | "value";
  href?: string;
};

type Props = {
  items: KpiItem[];
  title?: string;
  className?: string;
};

export function KpiStrip({ items, title, className = "" }: Props) {
  return (
    <section className={`v1-kpi-strip ${className}`.trim()} aria-label={title ?? "Indicadores clave"}>
      {title && <h3 className="v1-kpi-strip__title">{title}</h3>}
      <div className="v1-kpi-strip__grid">
        {items.map((item) => {
          const cls = `v1-kpi-card v1-kpi-card--${item.tone ?? "default"}`;
          const inner = (
            <>
              <span className="v1-kpi-card__label">{item.label}</span>
              <span className="v1-kpi-card__value">{item.value}</span>
              {item.hint && <span className="v1-kpi-card__hint">{item.hint}</span>}
            </>
          );
          if (item.href?.startsWith("/")) {
            return <Link key={item.id} to={item.href} className={cls}>{inner}</Link>;
          }
          if (item.href) {
            return <a key={item.id} href={item.href} className={cls}>{inner}</a>;
          }
          return <div key={item.id} className={cls}>{inner}</div>;
        })}
      </div>
    </section>
  );
}
