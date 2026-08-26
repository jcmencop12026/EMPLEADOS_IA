import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  activateAutomation,
  createAutomation,
  fetchAutomation,
  fetchEmployees,
  updateAutomation,
  type AutomationItem,
  type EmployeeItem,
} from "../api";

const STEPS = [
  "Identidad",
  "Objetivo",
  "Programación",
  "Empleado",
  "Límites",
  "Aprobación",
  "Revisar",
] as const;

type FormState = {
  name: string;
  description: string;
  objective: string;
  schedule_type: string;
  timezone: string;
  trigger_type: string;
  event_type: string;
  start_at: string;
  hour: number;
  minute: number;
  interval_minutes: number;
  employee_id: string;
  max_runs_per_day: number;
  max_retries: number;
  retry_delay_seconds: number;
  timeout_seconds: string;
  max_cost_per_run: string;
  estimated_cost: string;
  requires_approval: boolean;
  workflow_tool: string;
};

const defaultForm: FormState = {
  name: "",
  description: "",
  objective: "",
  schedule_type: "DAILY",
  timezone: "UTC",
  trigger_type: "SCHEDULE",
  event_type: "",
  start_at: "",
  hour: 9,
  minute: 0,
  interval_minutes: 60,
  employee_id: "",
  max_runs_per_day: 10,
  max_retries: 0,
  retry_delay_seconds: 60,
  timeout_seconds: "",
  max_cost_per_run: "",
  estimated_cost: "",
  requires_approval: false,
  workflow_tool: "docint",
};

function automationToForm(auto: AutomationItem): FormState {
  const rec = auto.recurrence || {};
  const wf = auto.workflow || {};
  const startLocal = auto.start_at
    ? new Date(auto.start_at).toISOString().slice(0, 16)
    : "";
  return {
    name: auto.name,
    description: auto.description || "",
    objective: auto.objective,
    schedule_type: auto.schedule_type || "DAILY",
    timezone: auto.timezone || "UTC",
    trigger_type: auto.trigger_type,
    event_type: rec.event_type || "",
    start_at: startLocal,
    hour: rec.hour ?? 9,
    minute: rec.minute ?? 0,
    interval_minutes: rec.interval_minutes ?? 60,
    employee_id: auto.employee_id || "",
    max_runs_per_day: auto.max_runs_per_day ?? 10,
    max_retries: auto.max_retries ?? 0,
    retry_delay_seconds: auto.retry_delay_seconds ?? 60,
    timeout_seconds: auto.timeout_seconds != null ? String(auto.timeout_seconds) : "",
    max_cost_per_run: auto.max_cost_per_run != null ? String(auto.max_cost_per_run) : "",
    estimated_cost: wf.estimated_cost != null ? String(wf.estimated_cost) : "",
    requires_approval: auto.requires_approval,
    workflow_tool: String(wf.tool || "docint"),
  };
}

export function AutomationWizardPage() {
  const navigate = useNavigate();
  const { automationId } = useParams<{ automationId: string }>();
  const isEdit = Boolean(automationId);
  const [step, setStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [employees, setEmployees] = useState<EmployeeItem[]>([]);
  const [form, setForm] = useState<FormState>(defaultForm);
  const [originalForm, setOriginalForm] = useState<FormState | null>(null);

  useEffect(() => {
    fetchEmployees().then(setEmployees).catch(() => setEmployees([]));
  }, []);

  useEffect(() => {
    if (!automationId) return;
    fetchAutomation(automationId)
      .then((auto) => {
        const loaded = automationToForm(auto);
        setForm(loaded);
        setOriginalForm(loaded);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "No se pudo cargar la automatización"));
  }, [automationId]);

  function validateStep(current: number): string | null {
    if (current === 0 && !form.name.trim()) return "Ingrese un nombre.";
    if (current === 1 && !form.objective.trim()) return "Ingrese el objetivo.";
    if (current === 2 && form.trigger_type === "SCHEDULE" && !form.schedule_type) return "Seleccione frecuencia.";
    if (current === 2 && form.trigger_type === "INTERNAL_EVENT" && !form.event_type.trim()) {
      return "Ingrese el tipo de evento interno.";
    }
    if (current === 4 && form.max_retries < 0) return "Los reintentos no pueden ser negativos.";
    if (current === 4 && form.max_retries > 10) return "Máximo 10 reintentos después del intento inicial.";
    return null;
  }

  function next() {
    const msg = validateStep(step);
    if (msg) {
      setError(msg);
      return;
    }
    setError(null);
    setStep((s) => Math.min(s + 1, STEPS.length - 1));
  }

  function prev() {
    setError(null);
    setStep((s) => Math.max(s - 1, 0));
  }

  function buildRecurrence() {
    if (form.trigger_type === "INTERNAL_EVENT") {
      return { event_type: form.event_type.trim() };
    }
    if (form.schedule_type === "INTERVAL") {
      return { interval_minutes: form.interval_minutes };
    }
    return { hour: form.hour, minute: form.minute };
  }

  function buildPayload() {
    const workflow: Record<string, unknown> = { tool: form.workflow_tool };
    if (form.estimated_cost) workflow.estimated_cost = Number(form.estimated_cost);
    return {
      name: form.name.trim(),
      description: form.description.trim() || null,
      objective: form.objective.trim(),
      trigger_type: form.trigger_type,
      schedule_type: form.trigger_type === "SCHEDULE" ? form.schedule_type : null,
      timezone: form.timezone,
      start_at: form.start_at ? new Date(form.start_at).toISOString() : null,
      recurrence: buildRecurrence(),
      employee_id: form.employee_id || null,
      requires_approval: form.requires_approval,
      max_runs_per_day: form.max_runs_per_day,
      max_retries: form.max_retries,
      retry_delay_seconds: form.retry_delay_seconds,
      timeout_seconds: form.timeout_seconds ? Number(form.timeout_seconds) : null,
      max_cost_per_run: form.max_cost_per_run ? Number(form.max_cost_per_run) : null,
      workflow,
    };
  }

  function buildPartialPayload(): Record<string, unknown> {
    if (!isEdit || !originalForm) return buildPayload();
    const payload: Record<string, unknown> = {};
    const cur = form;
    const orig = originalForm;

    if (cur.name.trim() !== orig.name) payload.name = cur.name.trim();
    if ((cur.description.trim() || null) !== (orig.description.trim() || null)) {
      payload.description = cur.description.trim() || null;
    }
    if (cur.objective.trim() !== orig.objective) payload.objective = cur.objective.trim();
    if (cur.trigger_type !== orig.trigger_type) payload.trigger_type = cur.trigger_type;
    if (cur.trigger_type === "SCHEDULE" && cur.schedule_type !== orig.schedule_type) {
      payload.schedule_type = cur.schedule_type;
    }
    if (cur.timezone !== orig.timezone) payload.timezone = cur.timezone;
    const startIso = cur.start_at ? new Date(cur.start_at).toISOString() : null;
    const origStartIso = orig.start_at ? new Date(orig.start_at).toISOString() : null;
    if (startIso !== origStartIso) payload.start_at = startIso;
    if (JSON.stringify(buildRecurrence()) !== JSON.stringify(buildRecurrenceFor(orig))) {
      payload.recurrence = buildRecurrence();
    }
    if ((cur.employee_id || null) !== (orig.employee_id || null)) payload.employee_id = cur.employee_id || null;
    if (cur.requires_approval !== orig.requires_approval) payload.requires_approval = cur.requires_approval;
    if (cur.max_runs_per_day !== orig.max_runs_per_day) payload.max_runs_per_day = cur.max_runs_per_day;
    if (cur.max_retries !== orig.max_retries) payload.max_retries = cur.max_retries;
    if (cur.retry_delay_seconds !== orig.retry_delay_seconds) payload.retry_delay_seconds = cur.retry_delay_seconds;
    const timeoutVal = cur.timeout_seconds ? Number(cur.timeout_seconds) : null;
    const origTimeout = orig.timeout_seconds ? Number(orig.timeout_seconds) : null;
    if (timeoutVal !== origTimeout) payload.timeout_seconds = timeoutVal;
    const costVal = cur.max_cost_per_run ? Number(cur.max_cost_per_run) : null;
    const origCost = orig.max_cost_per_run ? Number(orig.max_cost_per_run) : null;
    if (costVal !== origCost) payload.max_cost_per_run = costVal;

    const wfPatch: Record<string, unknown> = {};
    if (cur.workflow_tool !== orig.workflow_tool) wfPatch.tool = cur.workflow_tool;
    const est = cur.estimated_cost ? Number(cur.estimated_cost) : null;
    const origEst = orig.estimated_cost ? Number(orig.estimated_cost) : null;
    if (est !== origEst) wfPatch.estimated_cost = est;
    if (Object.keys(wfPatch).length > 0) payload.workflow = wfPatch;

    return payload;
  }

  function buildRecurrenceFor(state: FormState) {
    if (state.trigger_type === "INTERNAL_EVENT") return { event_type: state.event_type.trim() };
    if (state.schedule_type === "INTERVAL") return { interval_minutes: state.interval_minutes };
    return { hour: state.hour, minute: state.minute };
  }

  async function submit(activate: boolean) {
    for (let i = 0; i <= 4; i += 1) {
      const msg = validateStep(i);
      if (msg) {
        setError(msg);
        setStep(i);
        return;
      }
    }
    setLoading(true);
    setError(null);
    try {
      const payload = isEdit ? buildPartialPayload() : buildPayload();
      const saved = isEdit && automationId
        ? await updateAutomation(automationId, payload)
        : await createAutomation(payload as ReturnType<typeof buildPayload>);
      if (activate) await activateAutomation(saved.id);
      navigate("/automatizaciones");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al guardar");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="ops-page">
      <header className="page-header">
        <Link to="/automatizaciones" className="muted">← Automatizaciones</Link>
        <h1>{isEdit ? "Editar automatización" : "Nueva automatización"}</h1>
      </header>
      <div className="wizard-steps">
        {STEPS.map((label, i) => (
          <span key={label} className={`wizard-step ${i === step ? "active" : ""}`}>
            {i + 1}. {label}
          </span>
        ))}
      </div>
      <div className="panel form-panel">
        {step === 0 && (
          <>
            <label>Nombre *<input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
            <label>Descripción<input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></label>
          </>
        )}
        {step === 1 && (
          <label>Objetivo *<textarea rows={4} value={form.objective} onChange={(e) => setForm({ ...form, objective: e.target.value })} /></label>
        )}
        {step === 2 && (
          <>
            <label>Trigger
              <select value={form.trigger_type} onChange={(e) => setForm({ ...form, trigger_type: e.target.value })}>
                <option value="SCHEDULE">Programado</option>
                <option value="INTERNAL_EVENT">Evento interno</option>
              </select>
            </label>
            {form.trigger_type === "INTERNAL_EVENT" && (
              <label>Tipo de evento *
                <input
                  value={form.event_type}
                  onChange={(e) => setForm({ ...form, event_type: e.target.value })}
                  placeholder="ej. rips.validated"
                />
              </label>
            )}
            {form.trigger_type === "SCHEDULE" && (
              <>
                <label>Frecuencia
                  <select value={form.schedule_type} onChange={(e) => setForm({ ...form, schedule_type: e.target.value })}>
                    <option value="ONE_TIME">Una vez</option>
                    <option value="DAILY">Diaria</option>
                    <option value="WEEKLY">Semanal</option>
                    <option value="MONTHLY">Mensual</option>
                    <option value="INTERVAL">Intervalo</option>
                  </select>
                </label>
                <label>Inicio (opcional)<input type="datetime-local" value={form.start_at} onChange={(e) => setForm({ ...form, start_at: e.target.value })} /></label>
                {form.schedule_type === "INTERVAL" ? (
                  <label>Intervalo (minutos)<input type="number" min={1} value={form.interval_minutes} onChange={(e) => setForm({ ...form, interval_minutes: Number(e.target.value) })} /></label>
                ) : (
                  <>
                    <label>Hora<input type="number" min={0} max={23} value={form.hour} onChange={(e) => setForm({ ...form, hour: Number(e.target.value) })} /></label>
                    <label>Minuto<input type="number" min={0} max={59} value={form.minute} onChange={(e) => setForm({ ...form, minute: Number(e.target.value) })} /></label>
                  </>
                )}
                <label>Zona horaria<input value={form.timezone} onChange={(e) => setForm({ ...form, timezone: e.target.value })} /></label>
              </>
            )}
          </>
        )}
        {step === 3 && (
          <label>Empleado IA (opcional — automático si vacío)
            <select value={form.employee_id} onChange={(e) => setForm({ ...form, employee_id: e.target.value })}>
              <option value="">— Selección automática —</option>
              {employees.map((e) => (
                <option key={e.id} value={e.id}>{e.name} ({e.code})</option>
              ))}
            </select>
          </label>
        )}
        {step === 4 && (
          <>
            <label>Máx. ejecuciones/día<input type="number" min={1} value={form.max_runs_per_day} onChange={(e) => setForm({ ...form, max_runs_per_day: Number(e.target.value) })} /></label>
            <label>Reintentos (tras intento inicial)<input type="number" min={0} max={10} value={form.max_retries} onChange={(e) => setForm({ ...form, max_retries: Number(e.target.value) })} /></label>
            <label>Retardo entre reintentos (s)<input type="number" min={0} value={form.retry_delay_seconds} onChange={(e) => setForm({ ...form, retry_delay_seconds: Number(e.target.value) })} /></label>
            <label>Timeout (s, opcional)<input value={form.timeout_seconds} onChange={(e) => setForm({ ...form, timeout_seconds: e.target.value })} placeholder="Sin límite" /></label>
            <label>Costo máx./ejecución<input value={form.max_cost_per_run} onChange={(e) => setForm({ ...form, max_cost_per_run: e.target.value })} placeholder="Opcional" /></label>
            <label>Herramienta workflow
              <select value={form.workflow_tool} onChange={(e) => setForm({ ...form, workflow_tool: e.target.value })}>
                <option value="docint">DOCINT</option>
                <option value="rips">RIPS</option>
              </select>
            </label>
            <label>Costo estimado (pre-validación)<input value={form.estimated_cost} onChange={(e) => setForm({ ...form, estimated_cost: e.target.value })} placeholder="Opcional" /></label>
          </>
        )}
        {step === 5 && (
          <label>
            <input type="checkbox" checked={form.requires_approval} onChange={(e) => setForm({ ...form, requires_approval: e.target.checked })} />
            Requiere aprobación humana antes de ejecutar
          </label>
        )}
        {step === 6 && (
          <div className="review-box">
            <p><strong>{form.name}</strong></p>
            <p className="muted">{form.objective}</p>
            {form.trigger_type === "SCHEDULE" ? (
              <p>{form.schedule_type} · {form.hour}:{String(form.minute).padStart(2, "0")} {form.timezone}</p>
            ) : (
              <p>Evento: {form.event_type}</p>
            )}
            <p>Reintentos: {form.max_retries} · Timeout: {form.timeout_seconds || "—"} · Aprobación: {form.requires_approval ? "Sí" : "No"}</p>
          </div>
        )}
        {error && <p className="error" role="alert">{error}</p>}
        <div className="ops-actions">
          <button type="button" className="btn" onClick={() => navigate("/automatizaciones")}>Cancelar</button>
          {step > 0 && <button type="button" className="btn" onClick={prev}>Anterior</button>}
          {step < STEPS.length - 1 ? (
            <button type="button" className="btn primary" onClick={next}>Siguiente</button>
          ) : (
            <>
              <button type="button" className="btn" disabled={loading} onClick={() => submit(false)}>Guardar borrador</button>
              <button type="button" className="btn primary" disabled={loading} onClick={() => submit(true)}>Activar</button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
