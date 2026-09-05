import type { ReactNode } from "react";

type Props = {
  title: string;
  description?: string;
  children: ReactNode;
  className?: string;
};

export function FormSection({ title, description, children, className = "" }: Props) {
  return (
    <section className={`v1-form-section ${className}`.trim()}>
      <header className="v1-form-section__head">
        <h3>{title}</h3>
        {description && <p>{description}</p>}
      </header>
      <div className="v1-form-section__body">{children}</div>
    </section>
  );
}
