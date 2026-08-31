import { useEffect, useId, useRef, useState } from "react";

export type ContextualHelpSection = {
  title: string;
  body: string;
};

export type ContextualHelpContent = {
  screen: string;
  purpose: string;
  needs?: string;
  steps?: string[];
  example?: string;
  expected?: string;
  sections?: ContextualHelpSection[];
};

type Props = {
  content: ContextualHelpContent;
  label?: string;
  className?: string;
};

/** Ayuda contextual «? Ayuda» — explica pantalla, pasos y resultado esperado. */
export function ContextualHelp({ content, label = "Ayuda", className = "" }: Props) {
  const [open, setOpen] = useState(false);
  const panelId = useId();
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    function onClick(e: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        const btn = (e.target as HTMLElement).closest(".contextual-help-trigger");
        if (!btn) setOpen(false);
      }
    }
    document.addEventListener("keydown", onKey);
    document.addEventListener("mousedown", onClick);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("mousedown", onClick);
    };
  }, [open]);

  return (
    <div className={`contextual-help ${className}`.trim()} ref={panelRef}>
      <button
        type="button"
        className="contextual-help-trigger"
        aria-expanded={open}
        aria-controls={panelId}
        title={`${label}: ${content.screen}`}
        onClick={() => setOpen((v) => !v)}
      >
        ? {label}
      </button>
      {open && (
        <div id={panelId} className="contextual-help-panel" role="dialog" aria-label={content.screen}>
          <header className="contextual-help-header">
            <strong>{content.screen}</strong>
            <button type="button" className="btn-icon" onClick={() => setOpen(false)} aria-label="Cerrar ayuda">
              ×
            </button>
          </header>
          <div className="contextual-help-body">
            <section>
              <h4>¿Qué hace esta pantalla?</h4>
              <p>{content.purpose}</p>
            </section>
            {content.needs && (
              <section>
                <h4>¿Qué necesita?</h4>
                <p>{content.needs}</p>
              </section>
            )}
            {content.steps && content.steps.length > 0 && (
              <section>
                <h4>Pasos</h4>
                <ol>
                  {content.steps.map((step, i) => (
                    <li key={i}>{step}</li>
                  ))}
                </ol>
              </section>
            )}
            {content.example && (
              <section>
                <h4>Ejemplo</h4>
                <p className="muted">{content.example}</p>
              </section>
            )}
            {content.expected && (
              <section>
                <h4>Resultado esperado</h4>
                <p>{content.expected}</p>
              </section>
            )}
            {content.sections?.map((s) => (
              <section key={s.title}>
                <h4>{s.title}</h4>
                <p>{s.body}</p>
              </section>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
