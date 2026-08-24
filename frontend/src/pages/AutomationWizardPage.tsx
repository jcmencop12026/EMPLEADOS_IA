import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { activateAutomation, createAutomation } from "../api";

const STEPS = ["Identidad", "Qué hacer", "Cuándo", "Límites", "Revisar"];

export function AutomationWizardPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: "",
    description: "",
    objective: "",
    schedule_type: "DAILY",
    timezone: "UTC",
    trigger_type: "SCHEDULE",
    hour: 9,
    minute: 0,
    requires_approval: false,
    max_runs_per_day: 10,
  });

  const next = () => setStep((s) => Math.min(s + 1, STEPS.length - 1));
  const prev = () => setStep((s) => Math.max(s - 1, 0));

  const submit = async (activate: boolean) => {
    setError(null);
    try {
      const created = await createAutomation({
        name: form.name,
        description: form.description || null,
        objective: form.objective,
        trigger_type: form.trigger_type,
        schedule_type: form.schedule_type,
        timezone: form.timezone,
        recurrence: { hour: form.hour, minute: form.minute },
        requires_approval: form.requires_approval,
        max_runs_per_day: form.max_runs_per_day,
      });
      if (activate) await activateAutomation(created.id);
      navigate("/automatizaciones");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    }
  };

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Nueva automatización</h1>
        <p className="muted">Wizard compacto</p>
      </header>
      <div className="wizard-tabs">
        {STEPS.map((label, i) => (
          <span key={label} className={i === step ? "active" : ""}>
            {i + 1}. {label}
          </span>
        ))}
      </div>
      <div className="panel form-panel">
        {step === 0 && (
          <>
            <label>Nombre</label>
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <label>Descripción</label>
            <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </>
        )}
        {step === 1 && (
          <>
            <label>Qué debe hacer</label>
            <textarea rows={4} value={form.objective} onChange={(e) => setForm({ ...form, objective: e.target.value })} />
          </>
        )}
        {step === 2 && (
          <>
            <label>Frecuencia</label>
            <select value={form.schedule_type} onChange={(e) => setForm({ ...form, schedule_type: e.target.value })}>
              <option value="ONE_TIME">Una vez</option>
              <option value="DAILY">Diaria</option>
              <option value="WEEKLY">Semanal</option>
              <option value="MONTHLY">Mensual</option>
              <option value="INTERVAL">Intervalo</option>
            </select>
            <label>Hora</label>
            <input type="number" min={0} max={23} value={form.hour} onChange={(e) => setForm({ ...form, hour: Number(e.target.value) })} />
            <label>Minuto</label>
            <input type="number" min={0} max={59} value={form.minute} onChange={(e) => setForm({ ...form, minute: Number(e.target.value) })} />
            <label>Zona horaria</label>
            <input value={form.timezone} onChange={(e) => setForm({ ...form, timezone: e.target.value })} />
          </>
        )}
        {step === 3 && (
          <>
            <label>
              <input type="checkbox" checked={form.requires_approval} onChange={(e) => setForm({ ...form, requires_approval: e.target.checked })} />
              Requiere aprobación
            </label>
            <label>Máx ejecuciones por día</label>
            <input type="number" value={form.max_runs_per_day} onChange={(e) => setForm({ ...form, max_runs_per_day: Number(e.target.value) })} />
          </>
        )}
        {step === 4 && (
          <div className="review-box">
            <p>
              <strong>{form.name}</strong> — {form.schedule_type} {form.hour}:{String(form.minute).padStart(2, "0")} {form.timezone}
            </p>
            <p className="muted">{form.objective}</p>
          </div>
        )}
        {error && <p className="error">{error}</p>}
        <div className="ops-actions">
          {step > 0 && (
            <button type="button" className="btn" onClick={prev}>
              Atrás
            </button>
          )}
          {step < STEPS.length - 1 ? (
            <button type="button" className="btn primary" onClick={next}>
              Siguiente
            </button>
          ) : (
            <>
              <button type="button" className="btn" onClick={() => submit(false)}>
                Guardar borrador
              </button>
              <button type="button" className="btn primary" onClick={() => submit(true)}>
                Activar
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
