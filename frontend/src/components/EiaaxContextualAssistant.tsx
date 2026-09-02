import { FormEvent, useState } from "react";
import { useLocation } from "react-router-dom";
import { ApiError, submitWorkRequest, type PlanResult } from "../api";

const SUGGESTIONS = [
  "¿Qué está ocurriendo en esta vista?",
  "¿Qué requiere atención prioritaria?",
  "¿Qué oportunidades podemos presentar?",
  "¿Qué empleados IA recomienda activar?",
  "¿Cuál sería el costo estimado?",
  "¿Qué puedo mostrar al cliente?",
] as const;

type Props = {
  compact?: boolean;
  title?: string;
  context?: Record<string, unknown>;
};

export function EiaaxContextualAssistant({ compact = false, title = "Preguntar a EIAAX", context }: Props) {
  const location = useLocation();
  const [open, setOpen] = useState(!compact);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PlanResult | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await submitWorkRequest(query.trim(), {
        source: "contextual_assistant",
        path: location.pathname,
        ...context,
      });
      setResult(res);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo consultar a EIAAX");
    } finally {
      setLoading(false);
    }
  }

  function askSuggestion(text: string) {
    setQuery(text);
    setOpen(true);
  }

  return (
    <section className={`eiaax-assistant ${compact ? "eiaax-assistant--compact" : ""}`} aria-label={title}>
      <header className="eiaax-assistant-header">
        <div>
          <strong>{title}</strong>
          <p className="muted small">Copiloto contextual — propone, no ejecuta sin autorización.</p>
        </div>
        {compact && (
          <button type="button" className="btn small secondary" onClick={() => setOpen((v) => !v)}>
            {open ? "Ocultar" : "Abrir"}
          </button>
        )}
      </header>

      {open && (
        <>
          <div className="eiaax-assistant-suggestions">
            {SUGGESTIONS.map((s) => (
              <button key={s} type="button" className="btn small" onClick={() => askSuggestion(s)} disabled={loading}>
                {s}
              </button>
            ))}
          </div>
          <form className="eiaax-assistant-form" onSubmit={onSubmit}>
            <label>
              Consulta
              <textarea
                rows={compact ? 2 : 3}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Formule su pregunta sobre el contexto actual…"
                disabled={loading}
              />
            </label>
            {error && <p className="error">{error}</p>}
            <button type="submit" className="btn primary" disabled={loading || !query.trim()}>
              {loading ? "Analizando…" : "Consultar"}
            </button>
          </form>
          {result && (
            <div className="eiaax-assistant-result">
              <p><strong>Objetivo:</strong> {result.objective ?? "—"}</p>
              {result.summary && <p>{result.summary}</p>}
              {result.tasks?.length ? (
                <ol>
                  {result.tasks.slice(0, 5).map((task) => (
                    <li key={task.id}>{task.title}</li>
                  ))}
                </ol>
              ) : null}
            </div>
          )}
        </>
      )}
    </section>
  );
}
