import { useEffect, useState } from "react";
import {
  fetchEmployeeEvaluacion20,
  fetchEmployeeFicha20,
  fetchEmployeeSupervision20,
  updateEmployeeFicha20,
} from "../api";
import { AUTONOMY_LEVEL, label } from "../lib/labels";

type Props = { employeeId: string };

export function EmployeeFicha20Tab({ employeeId }: Props) {
  const [ficha, setFicha] = useState<Record<string, unknown> | null>(null);
  const [evaluacion, setEvaluacion] = useState<Record<string, unknown> | null>(null);
  const [supervision, setSupervision] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [autonomia, setAutonomia] = useState("EJECUTA_CON_APROBACION");
  const [mision, setMision] = useState("");
  const [saving, setSaving] = useState(false);

  function load() {
    Promise.all([
      fetchEmployeeFicha20(employeeId),
      fetchEmployeeEvaluacion20(employeeId),
      fetchEmployeeSupervision20(employeeId),
    ])
      .then(([f, e, s]) => {
        setFicha(f);
        setEvaluacion(e);
        setSupervision(s);
        setAutonomia(String(f.autonomia || "EJECUTA_CON_APROBACION"));
        setMision(String(f.mision || ""));
        setError(null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Error al cargar ficha 2.0"));
  }

  useEffect(() => {
    load();
  }, [employeeId]);

  async function onSave() {
    setSaving(true);
    try {
      const updated = await updateEmployeeFicha20(employeeId, { autonomia, mision });
      setFicha(updated);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo guardar");
    } finally {
      setSaving(false);
    }
  }

  if (!ficha) return <p className="muted">Cargando ficha laboral 2.0…</p>;

  const ciclo = ficha.ciclo_vida as Record<string, unknown> | undefined;
  const hallazgos = (evaluacion?.hallazgos as string[]) || [];

  return (
    <div className="employee-ficha-20">
      {error && <p className="error">{error}</p>}

      <div className="panel compact-panel">
        <h3>Ciclo de vida (misión)</h3>
        <p>
          <strong>Fase:</strong> {String(ciclo?.fase_mision ?? "—")} ·{" "}
          <strong>Estado API:</strong> {String(ciclo?.lifecycle_status ?? "—")} ·{" "}
          <strong>Versión:</strong> {String(ciclo?.version ?? "—")}
        </p>
        {ciclo?.shadow_mode ? <p className="badge demo-badge">MODO SOMBRA</p> : null}
      </div>

      <div className="form-grid">
        <label>
          Misión
          <textarea value={mision} onChange={(e) => setMision(e.target.value)} rows={2} />
        </label>
        <label>
          Nivel de autonomía
          <select value={autonomia} onChange={(e) => setAutonomia(e.target.value)}>
            {Object.keys(AUTONOMY_LEVEL).map((k) => (
              <option key={k} value={k}>
                {label(AUTONOMY_LEVEL, k)}
              </option>
            ))}
          </select>
        </label>
      </div>
      <button type="button" className="btn primary" onClick={onSave} disabled={saving}>
        {saving ? "Guardando…" : "Guardar ficha"}
      </button>

      <section className="panel">
        <h3>Capacidades y herramientas autorizadas</h3>
        <p className="muted small">Reutiliza asignaciones existentes — no duplica catálogo.</p>
        <ul>
          {((ficha.capacidades as Array<{ name: string; code: string }>) || []).map((c) => (
            <li key={c.code}>{c.name} ({c.code})</li>
          ))}
        </ul>
        <ul>
          {((ficha.herramientas_autorizadas as Array<{ code: string; permission: string }>) || []).map((t) => (
            <li key={t.code}>{t.code} — {t.permission}</li>
          ))}
        </ul>
      </section>

      <section className="panel">
        <h3>Evaluación esperado vs real</h3>
        {hallazgos.length > 0 ? (
          <ul>{hallazgos.map((h) => <li key={h}>{h}</li>)}</ul>
        ) : (
          <p className="muted">Sin alertas detectadas.</p>
        )}
        <p className="muted small">
          Costo acumulado: {String(evaluacion?.costo_acumulado ?? "—")} · Aprobaciones pendientes:{" "}
          {String(evaluacion?.aprobaciones_pendientes ?? 0)}
        </p>
      </section>

      <section className="panel">
        <h3>Supervisión reciente</h3>
        <p className="muted small">
          Eventos: {String((supervision?.resumen as Record<string, unknown>)?.total_eventos ?? 0)} · Errores:{" "}
          {String((supervision?.resumen as Record<string, unknown>)?.errores ?? 0)}
        </p>
      </section>
    </div>
  );
}
