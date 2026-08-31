import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  ApiError,
  createEmployee,
  fetchCapabilities,
  fetchEmployeeDetail,
  fetchTemplates,
  fetchTools,
  updateEmployee,
} from "../api";

const STEPS = ["Identidad", "Capacidades", "Herramientas", "Modelo", "Revisión"];

type WizardForm = {
  name: string;
  specialty: string;
  role: string;
  objective: string;
  template_code: string;
  capability_ids: string[];
  tool_ids: string[];
  model_provider: string;
  model_name: string;
};

function buildUpdatePayload(form: WizardForm, step: number): Record<string, unknown> {
  const payload: Record<string, unknown> = {
    name: form.name,
    role: form.role,
    objective: form.objective,
    specialty: form.specialty,
  };
  if (step >= 1 || form.capability_ids.length > 0) {
    payload.capability_ids = form.capability_ids;
  }
  if (step >= 2 || form.tool_ids.length > 0) {
    payload.tools = form.tool_ids.map((id) => ({ tool_id: id, permission: "ALLOW" }));
  }
  if (step >= 3 || form.model_name) {
    payload.model_policy = {
      preferred_provider: form.model_provider,
      preferred_model: form.model_name,
    };
  }
  return payload;
}

export function EmployeeWizardPage() {
  const navigate = useNavigate();
  const { employeeId: routeEmployeeId } = useParams<{ employeeId?: string }>();
  const isEdit = Boolean(routeEmployeeId);
  const [step, setStep] = useState(0);
  const [templates, setTemplates] = useState<Array<{ code: string; name: string; specialty: string }>>([]);
  const [capabilities, setCapabilities] = useState<Array<{ id: string; code: string; name: string }>>([]);
  const [tools, setTools] = useState<Array<{ id: string; code: string; name: string }>>([]);
  const [employeeId, setEmployeeId] = useState<string | null>(routeEmployeeId ?? null);
  const [form, setForm] = useState<WizardForm>({
    name: "",
    specialty: "",
    role: "",
    objective: "",
    template_code: "",
    capability_ids: [],
    tool_ids: [],
    model_provider: "rule-engine",
    model_name: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(isEdit);

  useEffect(() => {
    Promise.all([fetchTemplates(), fetchCapabilities(), fetchTools()])
      .then(([t, c, tl]) => {
        setTemplates(t);
        setCapabilities(c);
        setTools(tl);
      })
      .catch((e) => setError(e instanceof ApiError ? e.message : "Error al cargar datos del asistente."));
  }, []);

  useEffect(() => {
    if (!routeEmployeeId) return;
    setInitialLoading(true);
    fetchEmployeeDetail(routeEmployeeId)
      .then((detail) => {
        const caps = (detail.capabilities as Array<{ id?: string; code?: string }>) || [];
        const toolRows = (detail.tools as Array<{ id?: string }>) || [];
        const policy = detail.model_policy as { provider?: string; model?: string } | undefined;
        setForm({
          name: String(detail.name || ""),
          specialty: String(detail.specialty || ""),
          role: String(detail.role || detail.employee?.role || ""),
          objective: String(detail.objective || detail.employee?.objective || ""),
          template_code: "",
          capability_ids: caps.map((c) => c.id).filter((id): id is string => Boolean(id)),
          tool_ids: toolRows.map((t) => t.id).filter((id): id is string => Boolean(id)),
          model_provider: policy?.provider || String(detail.model_provider || "rule-engine"),
          model_name: policy?.model || String(detail.model_name || ""),
        });
        setEmployeeId(routeEmployeeId);
      })
      .catch((e) => setError(e instanceof ApiError ? e.message : "No se pudo cargar el empleado."))
      .finally(() => setInitialLoading(false));
  }, [routeEmployeeId]);

  async function saveDraft(): Promise<string | null> {
    setLoading(true);
    setError(null);
    try {
      if (!employeeId) {
        const created = await createEmployee({
          name: form.name,
          specialty: form.specialty,
          role: form.role,
          objective: form.objective,
          template_code: form.template_code || undefined,
        });
        const id = created.id as string;
        setEmployeeId(id);
        return id;
      }
      await updateEmployee(employeeId, buildUpdatePayload(form, step));
      return employeeId;
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "No se pudo guardar el borrador.");
      return null;
    } finally {
      setLoading(false);
    }
  }

  async function finish() {
    setLoading(true);
    setError(null);
    try {
      const id = employeeId ?? (await saveDraft());
      if (!id) {
        if (!form.name) setError("Ingrese un nombre para el empleado.");
        return;
      }
      if (!employeeId) {
        await updateEmployee(id, buildUpdatePayload(form, STEPS.length - 1));
      } else {
        await updateEmployee(id, buildUpdatePayload(form, STEPS.length - 1));
      }
      navigate(`/empleados/${id}`);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "No se pudo guardar el empleado.");
    } finally {
      setLoading(false);
    }
  }

  if (initialLoading) {
    return <p className="muted">Cargando empleado…</p>;
  }

  return (
    <div className="ops-page">
      <header className="page-header">
        <Link to={employeeId ? `/empleados/${employeeId}` : "/directorio"} className="muted">
          ← {employeeId ? "Detalle" : "Directorio"}
        </Link>
        <h1>Fábrica de Empleados IA — {isEdit ? "Editar" : "Crear"} Empleado IA</h1>
      </header>

      <div className="wizard-steps">
        {STEPS.map((s, i) => (
          <span key={s} className={`wizard-step ${i === step ? "active" : ""}`}>{s}</span>
        ))}
      </div>

      <section className="panel">
        {step === 0 && (
          <>
            {!isEdit && (
              <label>Plantilla (opcional)
                <select value={form.template_code} onChange={(e) => {
                  const t = templates.find((x) => x.code === e.target.value);
                  setForm({ ...form, template_code: e.target.value, specialty: t?.specialty || form.specialty, name: t?.name || form.name });
                }}>
                  <option value="">— Sin plantilla —</option>
                  {templates.map((t) => <option key={t.code} value={t.code}>{t.name}</option>)}
                </select>
              </label>
            )}
            <label>Nombre<input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
            <label>Especialidad<input value={form.specialty} onChange={(e) => setForm({ ...form, specialty: e.target.value })} /></label>
            <label>Rol<input value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} /></label>
            <label>Objetivo<textarea value={form.objective} onChange={(e) => setForm({ ...form, objective: e.target.value })} rows={2} /></label>
          </>
        )}
        {step === 1 && (
          <div className="check-grid">
            {capabilities.map((c) => (
              <label key={c.id} className="check-item">
                <input type="checkbox" checked={form.capability_ids.includes(c.id)} onChange={(e) => {
                  setForm({ ...form, capability_ids: e.target.checked ? [...form.capability_ids, c.id] : form.capability_ids.filter((x) => x !== c.id) });
                }} />
                {c.name} <span className="mono muted">({c.code})</span>
              </label>
            ))}
          </div>
        )}
        {step === 2 && (
          <div className="check-grid">
            {tools.map((t) => (
              <label key={t.id} className="check-item">
                <input type="checkbox" checked={form.tool_ids.includes(t.id)} onChange={(e) => {
                  setForm({ ...form, tool_ids: e.target.checked ? [...form.tool_ids, t.id] : form.tool_ids.filter((x) => x !== t.id) });
                }} />
                {t.name} <span className="mono muted">({t.code})</span>
              </label>
            ))}
          </div>
        )}
        {step === 3 && (
          <>
            <label>Proveedor<input value={form.model_provider} onChange={(e) => setForm({ ...form, model_provider: e.target.value })} /></label>
            <label>Modelo<input value={form.model_name} onChange={(e) => setForm({ ...form, model_name: e.target.value })} placeholder="rule-engine / ollama model" /></label>
            <p className="muted">Preferencia RULE/PYTHON/TOOL antes de LLM cuando resuelva correctamente.</p>
          </>
        )}
        {step === 4 && (
          <div className="review-box">
            <p><strong>{form.name}</strong> — {form.specialty}</p>
            <p className="muted">{form.role} · {form.objective}</p>
            <p>Capacidades: {form.capability_ids.length} · Herramientas: {form.tool_ids.length}</p>
            <p className="mono muted">{form.model_provider} / {form.model_name || "—"}</p>
          </div>
        )}
        {error && <p className="error">{error}</p>}
        <div className="ops-actions">
          {step > 0 && <button type="button" className="btn" onClick={() => setStep(step - 1)}>Atrás</button>}
          <button type="button" className="btn" disabled={loading} onClick={saveDraft}>Guardar borrador</button>
          {step < STEPS.length - 1 ? (
            <button type="button" className="btn primary" onClick={() => setStep(step + 1)}>Siguiente</button>
          ) : (
            <button type="button" className="btn primary" disabled={loading} onClick={finish}>
              {isEdit ? "Guardar cambios" : "Crear y configurar"}
            </button>
          )}
        </div>
      </section>
    </div>
  );
}
