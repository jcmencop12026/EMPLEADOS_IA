import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  createEmployee,
  fetchCapabilities,
  fetchTemplates,
  fetchTools,
  updateEmployee,
} from "../api";

const STEPS = ["Identidad", "Capabilities", "Herramientas", "Modelo", "Revisión"];

export function EmployeeWizardPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [templates, setTemplates] = useState<Array<{ code: string; name: string; specialty: string }>>([]);
  const [capabilities, setCapabilities] = useState<Array<{ id: string; code: string; name: string }>>([]);
  const [tools, setTools] = useState<Array<{ id: string; code: string; name: string }>>([]);
  const [employeeId, setEmployeeId] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: "",
    specialty: "",
    role: "",
    objective: "",
    template_code: "",
    capability_ids: [] as string[],
    tool_ids: [] as string[],
    model_provider: "rule-engine",
    model_name: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    Promise.all([fetchTemplates(), fetchCapabilities(), fetchTools()])
      .then(([t, c, tl]) => {
        setTemplates(t);
        setCapabilities(c);
        setTools(tl);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Error"));
  }, []);

  async function saveDraft() {
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
        setEmployeeId(created.id as string);
      } else {
        await updateEmployee(employeeId, {
          name: form.name,
          role: form.role,
          objective: form.objective,
          specialty: form.specialty,
          capability_ids: form.capability_ids,
          tools: form.tool_ids.map((id) => ({ tool_id: id, permission: "ALLOW" })),
          model_policy: { preferred_provider: form.model_provider, preferred_model: form.model_name },
        });
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    } finally {
      setLoading(false);
    }
  }

  async function finish() {
    await saveDraft();
    if (employeeId) navigate(`/empleados/${employeeId}`);
    else if (form.name) {
      const created = await createEmployee({ name: form.name, specialty: form.specialty, template_code: form.template_code || undefined });
      const id = created.id as string;
      await updateEmployee(id, {
        capability_ids: form.capability_ids,
        tools: form.tool_ids.map((tid) => ({ tool_id: tid, permission: "ALLOW" })),
        model_policy: { preferred_provider: form.model_provider, preferred_model: form.model_name },
      });
      navigate(`/empleados/${id}`);
    }
  }

  return (
    <div className="ops-page">
      <header className="page-header">
        <Link to="/directorio" className="muted">← Directorio</Link>
        <h1>Agent Factory — Crear Empleado IA</h1>
      </header>

      <div className="wizard-steps">
        {STEPS.map((s, i) => (
          <span key={s} className={`wizard-step ${i === step ? "active" : ""}`}>{s}</span>
        ))}
      </div>

      <section className="panel">
        {step === 0 && (
          <>
            <label>Plantilla (opcional)
              <select value={form.template_code} onChange={(e) => {
                const t = templates.find((x) => x.code === e.target.value);
                setForm({ ...form, template_code: e.target.value, specialty: t?.specialty || form.specialty, name: t?.name || form.name });
              }}>
                <option value="">— Sin plantilla —</option>
                {templates.map((t) => <option key={t.code} value={t.code}>{t.name}</option>)}
              </select>
            </label>
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
            <p>Capabilities: {form.capability_ids.length} · Herramientas: {form.tool_ids.length}</p>
          </div>
        )}
        {error && <p className="error">{error}</p>}
        <div className="ops-actions">
          {step > 0 && <button type="button" className="btn" onClick={() => setStep(step - 1)}>Atrás</button>}
          <button type="button" className="btn" disabled={loading} onClick={saveDraft}>Guardar borrador</button>
          {step < STEPS.length - 1 ? (
            <button type="button" className="btn primary" onClick={() => setStep(step + 1)}>Siguiente</button>
          ) : (
            <button type="button" className="btn primary" disabled={loading} onClick={finish}>Crear y configurar</button>
          )}
        </div>
      </section>
    </div>
  );
}
