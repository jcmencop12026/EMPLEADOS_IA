import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ApiError, type PlanResult, submitWorkRequest } from "../api";
import { label, EXECUTION_STATUS } from "../lib/labels";

type ProposedStep = {
  id: string;
  label: string;
  tipo: string;
  descripcion: string;
};

function inferProposal(query: string): { steps: ProposedStep[]; sectorSalud: boolean } {
  const q = query.toLowerCase();
  const sectorSalud = /rips|ips|salud|eps|hospital|clínica|clinica|docint|facturación salud/.test(q);
  const steps: ProposedStep[] = [
    { id: "info", label: "Recopilar información", tipo: "informacion", descripcion: "EIAAX solicita solo los datos necesarios según su necesidad." },
    { id: "diag", label: "Diagnóstico", tipo: "diagnostico", descripcion: "Analizar hallazgos, riesgos y oportunidades." },
  ];
  if (/empleado|asistente|agente/.test(q)) {
    steps.push({ id: "emp", label: "Empleado IA", tipo: "empleado", descripcion: "Reutilizar existente o proponer uno nuevo con capacidades adecuadas." });
  }
  if (/automatiz|workflow|proceso/.test(q)) {
    steps.push({ id: "auto", label: "Automatización", tipo: "automatizacion", descripcion: "Definir pasos, controles y aprobaciones." });
  }
  if (/integrac|conector|api/.test(q)) {
    steps.push({ id: "int", label: "Integración", tipo: "integracion", descripcion: "Conectar fuentes y sistemas relevantes." });
  }
  if (sectorSalud) {
    steps.push({ id: "salud", label: "Análisis sector salud", tipo: "salud", descripcion: "Validación RIPS/DOCINT cuando el contexto lo requiere." });
  }
  steps.push({ id: "auth", label: "Su autorización", tipo: "control", descripcion: "Revise, modifique y autorice antes de ejecutar." });
  return { steps, sectorSalud };
}

export function OperationsCenterPage() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PlanResult | null>(null);
  const [authorized, setAuthorized] = useState(false);
  const [editedSteps, setEditedSteps] = useState<ProposedStep[] | null>(null);

  const proposal = useMemo(() => inferProposal(query), [query]);
  const steps = editedSteps ?? proposal.steps;

  async function runAuthorized() {
    if (!query.trim()) {
      setError("Describa qué necesita hacer hoy.");
      return;
    }
    setLoading(true);
    setError(null);
    const context: Record<string, unknown> = {
      intent: "nueva_solicitud",
      proposed_steps: steps.map((s) => s.tipo),
      sector_salud: proposal.sectorSalud,
    };
    if (proposal.sectorSalud && /rips|facturación|validar/.test(query.toLowerCase())) {
      context.tool = "rips";
    }
    try {
      const res = await submitWorkRequest(query.trim(), context);
      setResult(res);
      setAuthorized(false);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Error al procesar la solicitud.");
    } finally {
      setLoading(false);
    }
  }

  function toggleStep(id: string) {
    setEditedSteps((prev) => {
      const base = prev ?? proposal.steps;
      if (base.some((s) => s.id === id)) {
        const next = base.filter((s) => s.id !== id);
        return next.length ? next : base;
      }
      const restored = proposal.steps.find((s) => s.id === id);
      return restored ? [...base, restored] : base;
    });
  }

  return (
    <div className="ops-page nueva-solicitud-page">
      <header className="page-header compact">
        <h1>Nueva solicitud</h1>
        <p className="muted">
          Expresar necesidad — EIAAX interpreta el contexto y propone pasos. Usted revisa, modifica y autoriza.
        </p>
        <p><Link to="/operaciones">← Centro de Operaciones</Link></p>
      </header>

      <section className="panel compact-panel ops-main">
        <label className="ops-label" htmlFor="ops-query">
          ¿Qué necesita hacer hoy?
        </label>
        <textarea
          id="ops-query"
          className="ops-input"
          rows={4}
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setEditedSteps(null);
            setResult(null);
          }}
          placeholder="Ej.: Necesito entender por qué la facturación de la IPS está rechazando RIPS y qué empleado IA puede ayudar."
        />

        {query.trim().length > 10 && (
          <section className="solicitud-propuesta panel-inner">
            <h2 className="section-title">Propuesta de EIAAX</h2>
            <p className="muted small">Pasos sugeridos según su necesidad. Desmarque lo que no aplique.</p>
            <ul className="solicitud-steps">
              {proposal.steps.map((step) => {
                const active = steps.some((s) => s.id === step.id);
                return (
                  <li key={step.id} className={active ? "active" : "inactive"}>
                    <label>
                      <input
                        type="checkbox"
                        checked={active}
                        onChange={() => toggleStep(step.id)}
                      />
                      <strong>{step.label}</strong>
                      <span className="muted small">{step.descripcion}</span>
                    </label>
                  </li>
                );
              })}
            </ul>
            {proposal.sectorSalud && (
              <p className="muted small salud-context-note">
                Contexto salud detectado — herramientas RIPS/DOCINT solo si son necesarias para su caso.
              </p>
            )}
          </section>
        )}

        <div className="ops-actions solicitud-actions">
          <button
            type="button"
            className="btn primary"
            disabled={loading || !query.trim()}
            onClick={() => setAuthorized(true)}
          >
            Revisar propuesta
          </button>
          {authorized && (
            <button type="button" className="btn primary" disabled={loading} onClick={() => void runAuthorized()}>
              {loading ? "Procesando…" : "Autorizar y ejecutar"}
            </button>
          )}
          <Link className="btn secondary" to="/evaluaciones">Ir a evaluaciones</Link>
          <Link className="btn secondary" to="/directorio">Ver empleados IA</Link>
        </div>
        {error && <p className="error">{error}</p>}
      </section>

      {result && (
        <section className="panel result-panel compact-panel">
          <div className="result-header">
            <h2>Resultado</h2>
            <span className={`badge status-${result.status}`} title={result.status}>
              {label(EXECUTION_STATUS, result.status)}
            </span>
          </div>
          <p>{result.summary || result.objective}</p>
          {result.confidence != null && (
            <p className="muted">Confianza: {(result.confidence * 100).toFixed(0)}%</p>
          )}
          {result.approval_status === "PENDING" && (
            <p className="warn">Esperando aprobación humana — ver Ejecuciones o Aprobaciones.</p>
          )}
          {result.result?.findings && result.result.findings.length > 0 && (
            <table className="data-table compact-table">
              <thead>
                <tr>
                  <th>Severidad</th>
                  <th>Código</th>
                  <th>Hallazgo</th>
                </tr>
              </thead>
              <tbody>
                {result.result.findings.map((f, i) => (
                  <tr key={i}>
                    <td>{f.severity}</td>
                    <td className="mono">{f.code}</td>
                    <td>{f.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <p>
            <Link className="btn link" to={`/ejecuciones/${result.plan_id}`}>Ver trazabilidad</Link>
            {" · "}
            <Link to="/aprobaciones">Aprobaciones</Link>
          </p>
        </section>
      )}
    </div>
  );
}
