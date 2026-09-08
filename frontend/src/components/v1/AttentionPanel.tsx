import type { ReactNode } from "react";
import { Link } from "react-router-dom";

export type AttentionItem = {
  id: string;
  title: string;
  detail?: string;
  href: string;
  priority?: "alta" | "media" | "baja";
};

type Props = {
  title?: string;
  items: AttentionItem[];
  emptyMessage?: string;
  className?: string;
};

export function AttentionPanel({
  title = "Requiere atención",
  items,
  emptyMessage = "Sin asuntos críticos pendientes en este contexto.",
  className = "",
}: Props) {
  const hasItems = items.length > 0;
  return (
    <section
      className={`v1-attention-panel ${hasItems ? "v1-attention-panel--active" : ""} ${className}`.trim()}
      aria-label={title}
    >
      <h3 className="v1-attention-panel__title">{title}</h3>
      {!hasItems ? (
        <p className="v1-attention-panel__empty">{emptyMessage}</p>
      ) : (
        <ul className="v1-attention-panel__list">
          {items.map((item) => (
            <li key={item.id} className={`v1-attention-item v1-attention-item--${item.priority ?? "media"}`}>
              <Link to={item.href} className="v1-attention-item__link">
                <strong>{item.title}</strong>
                {item.detail && <span className="v1-attention-item__detail">{item.detail}</span>}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
