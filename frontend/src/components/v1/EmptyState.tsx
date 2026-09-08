import type { ReactNode } from "react";

type Props = {
  title: string;
  description: string;
  action?: ReactNode;
  icon?: ReactNode;
  className?: string;
};

export function EmptyState({ title, description, action, icon, className = "" }: Props) {
  return (
    <div className={`v1-empty-state ${className}`.trim()} role="status">
      {icon && <div className="v1-empty-state__icon">{icon}</div>}
      <h4 className="v1-empty-state__title">{title}</h4>
      <p className="v1-empty-state__desc">{description}</p>
      {action && <div className="v1-empty-state__action">{action}</div>}
    </div>
  );
}
