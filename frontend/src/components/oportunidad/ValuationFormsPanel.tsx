import { FormEvent, useState } from "react";
import type { ValuationSummary } from "../../api";
import { labelOportunidad, SCENARIO_TYPE, VALUE_NATURE, VALUATION_STATUS } from "../../lib/oportunidadLabels";

type Props = {
  canManage: boolean;
  canValidate: boolean;
  onCreate: () => Promise<void>;
  onExpected: (data: { gross_value: string; probability: string; assumptions: string }) => Promise<void>;
  onScenario: (tipo: string, data: { value_amount: string; probability: string; assumptions: string }) => Promise<void>;
  onReal: (data: { materialized_value: string; evidence: string }) => Promise<void>;
  onCost: (data: { amount: string; description: string }) => Promise<void>;
  onValidate: () => Promise<void>;
  valuation: ValuationSummary | null;
};

type FormMode = "none" | "expected" | "scenario" | "real" | "cost";

export function ValuationFormsPanel({
  canManage,
  canValidate,
  onCreate,
  onExpected,
  onScenario,
  onReal,
  onCost,
  onValidate,
  valuation,
}: Props) {
  const [mode, setMode] = useState<FormMode>("none");
  const [scenarioTipo, setScenarioTipo] = useState("BASE");
  const [gross, setGross] = useState("");
  const [probability, setProbability] = useState("");
  const [assumptions, setAssumptions] = useState("");
  const [amount, setAmount] = useState("");
  const [evidence, setEvidence] = useState("");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      if (mode === "expected") {
        await onExpected({ gross_value: gross, probability, assumptions });
      } else if (mode === "scenario") {
        await onScenario(scenarioTipo, { value_amount: amount, probability, assumptions });
      } else if (mode === "real") {
        await onReal({ materialized_value: amount, evidence });
      } else if (mode === "cost") {
        await onCost({ amount, description });
      }
      setMode("none");
      setGross("");
      setProbability("");
      setAssumptions("");
      setAmount("");
      setEvidence("");
      setDescription("");
    } finally {
      setBusy(false);
    }
  }

  if (!valuation?.has_valuation) {
    return (
      <div className="valuation-empty">
        <p className="muted">Sin valoración económica registrada para esta oportunidad.</p>
        {canManage && (
          <button type="button" className="btn primary" disabled={busy} onClick={() => { setBusy(true); onCreate().finally(() => setBusy(false)); }}>
            Crear valoración
          </button>
        )}
      </div>
    );
  }

  const v = valuation.valuation;

  return (
    <div className="valuation-panel stack-gap">
      {canManage && (
        <div className="toolbar compact-toolbar valuation-actions">
          <button type="button" className="btn secondary small" onClick={() => setMode("expected")}>Valor esperado</button>
          <button type="button" className="btn secondary small" onClick={() => { setScenarioTipo("CONSERVADOR"); setMode("scenario"); }}>Esc. conservador</button>
          <button type="button" className="btn secondary small" onClick={() => { setScenarioTipo("BASE"); setMode("scenario"); }}>Esc. base</button>
          <button type="button" className="btn secondary small" onClick={() => { setScenarioTipo("OPTIMISTA"); setMode("scenario"); }}>Esc. optimista</button>
          <button type="button" className="btn secondary small" onClick={() => setMode("real")}>Valor real</button>
          <button type="button" className="btn secondary small" onClick={() => setMode("cost")}>Costo ejecución</button>
          {canValidate && (
            <button type="button" className="btn primary small" disabled={busy} onClick={() => { setBusy(true); onValidate().finally(() => setBusy(false)); }}>
              Validar valoración
            </button>
          )}
        </div>
      )}

      {mode !== "none" && canManage && (
        <form className="compact-form valuation-form panel-inner" onSubmit={submit}>
          <h3 className="section-title">
            {mode === "expected" && "Registrar valor esperado"}
            {mode === "scenario" && `Escenario ${labelOportunidad(SCENARIO_TYPE, scenarioTipo)}`}
            {mode === "real" && "Registrar valor real materializado"}
            {mode === "cost" && "Registrar costo de ejecución"}
          </h3>
          {mode === "scenario" && (
            <label>
              Escenario
              <select value={scenarioTipo} onChange={(e) => setScenarioTipo(e.target.value)}>
                {Object.entries(SCENARIO_TYPE).map(([k, lbl]) => (
                  <option key={k} value={k}>{lbl}</option>
                ))}
              </select>
            </label>
          )}
          {(mode === "expected") && (
            <label>
              Valor bruto esperado
              <input type="number" min={0} step={1} required value={gross} onChange={(e) => setGross(e.target.value)} />
            </label>
          )}
          {(mode === "scenario" || mode === "real" || mode === "cost") && (
            <label>
              {mode === "cost" ? "Monto del costo" : "Valor"}
              <input type="number" min={0} step={1} required value={amount} onChange={(e) => setAmount(e.target.value)} />
            </label>
          )}
          {(mode === "expected" || mode === "scenario") && (
            <>
              <label>
                Probabilidad (0–1)
                <input type="number" min={0} max={1} step={0.01} required value={probability} onChange={(e) => setProbability(e.target.value)} />
              </label>
              <label>
                Supuestos / evidencia
                <textarea rows={2} value={assumptions} onChange={(e) => setAssumptions(e.target.value)} placeholder="Base de la estimación" />
              </label>
            </>
          )}
          {mode === "real" && (
            <label>
              Evidencia de medición
              <textarea rows={2} value={evidence} onChange={(e) => setEvidence(e.target.value)} required />
            </label>
          )}
          {mode === "cost" && (
            <label>
              Descripción del costo
              <input type="text" value={description} onChange={(e) => setDescription(e.target.value)} required />
            </label>
          )}
          <div className="form-actions-row">
            <button type="submit" className="btn primary" disabled={busy}>Guardar</button>
            <button type="button" className="btn secondary" onClick={() => setMode("none")}>Cancelar</button>
          </div>
        </form>
      )}

      <dl className="detail-grid">
        <dt>Tipo de valor</dt>
        <dd>{v?.value_type ?? "—"} ({v?.scope ?? "—"})</dd>
        <dt>Estado</dt>
        <dd>{labelOportunidad(VALUATION_STATUS, v?.status)} · v{v?.version ?? "—"}</dd>
        <dt className="highlight-esperado">Valor esperado ajustado</dt>
        <dd>{valuation.adjusted_expected ?? "—"} <span className="badge">Esperado</span></dd>
        <dt>Valor bruto esperado</dt>
        <dd>{valuation.gross_expected ?? "—"}</dd>
        <dt className="highlight-real">Valor materializado</dt>
        <dd>{valuation.materialized_value ?? "—"} <span className="badge">Real</span></dd>
        <dt>Valor atribuible</dt>
        <dd>
          {valuation.attributable_value ?? "—"}
          {valuation.real?.value_nature && (
            <span className="badge"> {labelOportunidad(VALUE_NATURE, valuation.real.value_nature)}</span>
          )}
        </dd>
        <dt>Costo total ejecución</dt>
        <dd>{valuation.total_execution_cost ?? "—"} (IA: {valuation.finops_ia_cost_label ?? "—"})</dd>
      </dl>
    </div>
  );
}
