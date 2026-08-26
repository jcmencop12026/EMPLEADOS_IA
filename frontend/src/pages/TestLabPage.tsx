import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { EmployeeItem, TestLabRun } from "../api";
import {
  fetchCapabilitiesCatalog,
  fetchEmployees,
  fetchKnowledgeCatalog,
  fetchTestLabRuns,
  fetchToolsCatalog,
  runTestLab,
} from "../api";

const SAMPLE_DOC = {
  documents: [{
    id: "d1",
    tipo_documento: "CC",
    numero_documento: "1234567890",
    fecha: "2026-01-01",
    contenido: "Documento de prueba Test Lab con contenido suficiente para análisis",
  }],
};

export function TestLabPage() {
  const [employees, setEmployees] = useState<EmployeeItem[]>([]);
  const [caps, setCaps] = useState<{ id: string; code: string; name: string }[]>([]);
  const [tools, setTools] = useState<{ id: string; code: string; name: string }[]>([]);
  const [knowledge, setKnowledge] = useState<{ id: string; name: string }[]>([]);
  const [runs, setRuns] = useState<TestLabRun[]>([]);
  const [result, setResult] = useState<TestLabRun | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [pageLoading, setPageLoading] = useState(true);
  const [form, setForm] = useState({
    employee_id: "",
    capability_id: "",
    tool_id: "",
    knowledge_source_ids: [] as string[],
    task_description: "Analizar documentos de prueba y reportar hallazgos",
  });

  useEffect(() => {
    Promise.all([
      fetchEmployees(),
      fetchCapabilitiesCatalog(),
      fetchToolsCatalog(),
      fetchKnowledgeCatalog(),
      fetchTestLabRuns(),
    ])
      .then(([emps, c, t, k, r]) => {
        setEmployees(emps);
        setCaps(c.filter((x) => x.status === "ACTIVA"));
        setTools(t.filter((x) => x.status === "ACTIVA"));
        setKnowledge(k.filter((x) => x.status === "ACTIVA"));
        setRuns(r);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar Test Lab"))
      .finally(() => setPageLoading(false));
  }, []);

  async function handleRun(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const run = await runTestLab({
        employee_id: form.employee_id,
        capability_id: form.capability_id || undefined,
        tool_id: form.tool_id || undefined,
        knowledge_source_ids: form.knowledge_source_ids.length ? form.knowledge_source_ids : undefined,
        task_description: form.task_description,
        context: { tool: "docint", ...SAMPLE_DOC },
      });
      setResult(run);
      setRuns(await fetchTestLabRuns());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al ejecutar prueba");
    } finally {
      setLoading(false);
    }
  }

  if (pageLoading) return <p className="muted">Cargando Test Lab…</p>;

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Test Lab</h1>
        <p className="muted">Pruebe un Empleado IA antes de certificar o activar — motor real de orquestación</p>
      </header>

      <form className="panel form-grid" onSubmit={handleRun}>
        <label>
          Empleado IA
          <select required value={form.employee_id} onChange={(e) => setForm({ ...form, employee_id: e.target.value })}>
            <option value="">Seleccionar…</option>
            {employees.map((e) => <option key={e.id} value={e.id}>{e.name} ({e.code})</option>)}
          </select>
        </label>
        <label>
          Capacidad
          <select value={form.capability_id} onChange={(e) => setForm({ ...form, capability_id: e.target.value })}>
            <option value="">Automática</option>
            {caps.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </label>
        <label>
          Herramienta
          <select value={form.tool_id} onChange={(e) => setForm({ ...form, tool_id: e.target.value })}>
            <option value="">Automática</option>
            {tools.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
          </select>
        </label>
        <label>
          Fuentes de conocimiento
          <select
            multiple
            value={form.knowledge_source_ids}
            onChange={(e) => setForm({
              ...form,
              knowledge_source_ids: Array.from(e.target.selectedOptions).map((o) => o.value),
            })}
          >
            {knowledge.map((k) => <option key={k.id} value={k.id}>{k.name}</option>)}
          </select>
        </label>
        <label>
          Tarea / prueba
          <textarea required rows={3} value={form.task_description} onChange={(e) => setForm({ ...form, task_description: e.target.value })} />
        </label>
        <button type="submit" className="btn primary" disabled={loading}>
          {loading ? "Ejecutando…" : "Ejecutar prueba"}
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      {result && (
        <section className="panel">
          <h2>Resultado</h2>
          <p><strong>Estado:</strong> {result.status}</p>
          <p><strong>Empleado:</strong> {result.employee_name || result.employee_id}</p>
          <p><strong>Capacidad:</strong> {result.capability_code || "—"}</p>
          <p><strong>Herramienta:</strong> {result.tool_code || "—"}</p>
          <p><strong>Duración:</strong> {result.duration_ms != null ? `${result.duration_ms} ms` : "—"}</p>
          <p><strong>Coste:</strong> {result.cost_label || "No disponible"}</p>
          <p><strong>WorkPlan:</strong> {result.work_plan_id ? <Link to={`/ejecuciones/${result.work_plan_id}`}>{result.work_plan_id}</Link> : "—"}</p>
          {result.approval_id && <p><strong>Aprobación:</strong> {result.approval_id} (ESPERANDO_APROBACION)</p>}
          {result.error_message && <p className="error">{result.error_message}</p>}
          {result.result && (
            <details>
              <summary>Detalle técnico</summary>
              <pre className="mono result-pre">{JSON.stringify(result.result, null, 2)}</pre>
            </details>
          )}
        </section>
      )}

      <section className="panel table-wrap">
        <h2>Historial reciente</h2>
        {runs.length === 0 ? (
          <p className="muted">Sin ejecuciones previas.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr><th>Fecha</th><th>Empleado</th><th>Estado</th><th>Duración</th><th>WorkPlan</th></tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr key={r.id}>
                  <td className="mono">{r.created_at?.slice(0, 19)}</td>
                  <td>{r.employee_name || r.employee_id}</td>
                  <td><span className="badge">{r.status}</span></td>
                  <td>{r.duration_ms != null ? `${r.duration_ms} ms` : "—"}</td>
                  <td>{r.work_plan_id ? <Link to={`/ejecuciones/${r.work_plan_id}`}>Ver</Link> : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
