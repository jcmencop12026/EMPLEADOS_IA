import { FormEvent, useState } from "react";
import { useLocation } from "react-router-dom";
import { ApiError, submitWorkRequest, type PlanResult } from "../api";
import type { AssistantIntent } from "../context/ContextualAssistantContext";

const SUGGESTIONS: Record<string, string[]> = {
  preguntar: [
    "¿Qué está ocurriendo en esta vista?",
    "¿Qué requiere atención prioritaria?",
    "¿Qué puedo mostrar al cliente?",
  ],
  analizar: [
    "Analice el estado actual y sus causas probables.",
    "¿Qué patrones detecta en los datos visibles?",
  ],
  proponer: [
    "¿Qué empleados IA recomienda activar?",
    "Proponga la siguiente mejor acción gobernada.",
  ],
  explicar: [
    "Explique este resultado en lenguaje ejecutivo.",
    "¿Por qué EIAAX sugiere esta priorización?",
  ],
  riesgos: [
    "¿Qué riesgos operativos o de cumplimiento detecta?",
    "¿Qué controles deberían reforzarse?",
  ],
  oportunidades: [
    "¿Qué oportunidades podemos presentar?",
    "¿Cuál es el valor potencial no capturado?",
  ],
  comparar: [
    "Compare antes, proyectado y real.",
    "¿Cómo se compara el consumo vs el presupuesto?",
  ],
  siguiente_accion: [
    "¿Cuál es el siguiente paso recomendado?",
    "¿Qué debería preparar para la empresa?",
  ],
};

const INTENT_LABELS: Record<AssistantIntent, string> = {
  preguntar: "Preguntar",
  analizar: "Analizar",
  proponer: "Proponer",
  explicar: "Explicar",
  riesgos: "Riesgos",
  oportunidades: "Oportunidades",
  comparar: "Comparar",
  siguiente_accion: "Siguiente acción",
};

type Props = {
  compact?: boolean;
  title?: string;
  context?: Record<string, unknown>;
};

export function EiaaxContextualAssistant({ compact = false, title = "Preguntar a EIAAX", context }: Props) {
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const [intent, setIntent] = useState<AssistantIntent>("preguntar");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PlanResult | null>(null);

  const suggestions = SUGGESTIONS[intent] ?? SUGGESTIONS.preguntar;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await submitWorkRequest(query.trim(), {
        source: "contextual_assistant",
        intent,
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

  if (compact && !open) {
    return (
      <button
        type="button"
        className="eiaax-assistant-fab btn secondary"
        onClick={() => setOpen(true)}
        aria-label={title}
        title={title}
      >
        EIAAX
      </button>
    );
  }

  return (
    <section
      className={`eiaax-assistant ${compact ? "eiaax-assistant--compact" : ""} ${open ? "eiaax-assistant--open" : ""}`}
      aria-label={title}
    >
      <header className="eiaax-assistant-header">
        <div>
          <strong>{title}</strong>
          <p className="muted small">Copiloto contextual — {INTENT_LABELS[intent].toLowerCase()}; propone, no ejecuta sin autorización.</p>
        </div>
        {compact && (
          <button type="button" className="btn small secondary" onClick={() => setOpen((v) => !v)}>
            {open ? "Ocultar" : "Abrir"}
          </button>
        )}
      </header>

      {open && (
        <>
          <div className="eiaax-assistant-intents" role="tablist" aria-label="Tipo de consulta">
            {(Object.keys(INTENT_LABELS) as AssistantIntent[]).map((key) => (
              <button
                key={key}
                type="button"
                role="tab"
                aria-selected={intent === key}
                className={`btn small ${intent === key ? "primary" : "secondary"}`}
                onClick={() => setIntent(key)}
              >
                {INTENT_LABELS[key]}
              </button>
            ))}
          </div>
          <div className="eiaax-assistant-suggestions">
            {suggestions.map((s) => (
              <button key={s} type="button" className="btn small secondary" onClick={() => askSuggestion(s)} disabled={loading}>
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
