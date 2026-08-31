import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { createEvaluacion, fetchEvaluaciones, type EvaluacionExpedienteSummary } from "../api";
import { usePermissions } from "../hooks/usePermissions";

const ESTADOS = ["", "BORRADOR", "EN_CURSO", "PRELIMINAR", "DIAGNOSTICA", "PROFUNDA", "CERRADO"] as const;

export function EvaluacionesPage() {
  const { has } = usePermissions();
  const [items, setItems] = useState<EvaluacionExpedienteSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busqueda, setBusqueda] = useState("");
  const [filtroEstado, setFiltroEstado] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    titulo: "",
    entidad_nombre: "",
    necesidad: "",
    objetivo: "",
    area_proceso: "",
    nivel: "PRELIMINAR",
  });

  function load() {
    const params = new URLSearchParams();
    if (busqueda) params.set("q", busqueda);
    if (filtroEstado) params.set("estado", filtroEstado);
    setLoading(true);
    fetchEvaluaciones(params.toString())
      .then((r) => { setItems(r.items); setTotal(r.total); setError(null); })
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar"))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, [busqueda, filtroEstado]);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    try {
      const created = await createEvaluacion(form);
      window.location.href = `/evaluaciones/${created.id}`;
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo crear la evaluación");
    }
  }

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Evaluaciones EIAAX</h1>
        <p className="muted">Expedientes de evaluación empresarial — entidad, información, análisis e impacto</p>
      </header>

      {error && <p className="error">{error}</p>}

      <div className="panel compact-panel filters-row">
        <input
          type="search"
          placeholder="Buscar por código, título o entidad…"
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
        />
        <select value={filtroEstado} onChange={(e) => setFiltroEstado(e.target.value)}>
          {ESTADOS.map((s) => (
            <option key={s || "all"} value={s}>{s || "Todos los estados"}</option>
          ))}
        </select>
        {has("evaluacion.manage") && (
          <button type="button" className="btn primary" onClick={() => setShowForm((v) => !v)}>
            {showForm ? "Cancelar" : "Nueva evaluación"}
          </button>
        )}
      </div>

      {showForm && has("evaluacion.manage") && (
        <form className="panel compact-panel eval-create-form" onSubmit={onCreate}>
          <h2>Nueva evaluación</h2>
          <div className="form-grid">
            <label>Título<input required value={form.titulo} onChange={(e) => setForm({ ...form, titulo: e.target.value })} /></label>
            <label>Entidad<input required value={form.entidad_nombre} onChange={(e) => setForm({ ...form, entidad_nombre: e.target.value })} /></label>
            <label>Área/proceso<input value={form.area_proceso} onChange={(e) => setForm({ ...form, area_proceso: e.target.value })} /></label>
            <label>Nivel
              <select value={form.nivel} onChange={(e) => setForm({ ...form, nivel: e.target.value })}>
                <option value="PRELIMINAR">Preliminar</option>
                <option value="DIAGNOSTICA">Diagnóstica</option>
                <option value="PROFUNDA">Profunda</option>
              </select>
            </label>
          </div>
          <label>Problema / necesidad<textarea rows={2} value={form.necesidad} onChange={(e) => setForm({ ...form, necesidad: e.target.value })} /></label>
          <label>Objetivo<textarea rows={2} value={form.objetivo} onChange={(e) => setForm({ ...form, objetivo: e.target.value })} /></label>
          <button type="submit" className="btn primary">Crear expediente</button>
        </form>
      )}

      {loading ? <p className="muted">Cargando…</p> : (
        <div className="panel compact-panel">
          <p className="muted">{total} expediente(s)</p>
          <table className="data-table compact-table">
            <thead>
              <tr>
                <th>Código</th>
                <th>Evaluación</th>
                <th>Entidad</th>
                <th>Estado</th>
                <th>Info %</th>
                <th>Confianza</th>
                <th>Nivel</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td><Link to={`/evaluaciones/${item.id}`}>{item.codigo}</Link></td>
                  <td>{item.titulo}</td>
                  <td>{item.entidad_nombre}</td>
                  <td>{item.estado}</td>
                  <td>{item.porcentaje_informacion}%</td>
                  <td>{item.confianza_global}</td>
                  <td>{item.nivel}</td>
                </tr>
              ))}
              {!items.length && (
                <tr><td colSpan={7} className="muted">Sin expedientes. Cree una evaluación para comenzar.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
