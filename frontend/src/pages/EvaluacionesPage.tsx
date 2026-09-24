import { FormEvent, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { createEntidadExterna, createEvaluacion, fetchEntidadExterna, fetchEvaluaciones, setPublicacionEstado, syncInformacionExpediente, type EvaluacionExpedienteSummary } from "../api";
import { usePermissions } from "../hooks/usePermissions";

const ESTADOS = ["", "BORRADOR", "EN_CURSO", "PRELIMINAR", "DIAGNOSTICA", "PROFUNDA", "CERRADO"] as const;

export function EvaluacionesPage() {
  const { has } = usePermissions();
  const [searchParams] = useSearchParams();
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
    sector: "",
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

  useEffect(() => {
    if (searchParams.get("nuevo") !== "1") return;
    const area = searchParams.get("area") ?? "";
    const temas = searchParams.get("temas") ?? "";
    const sector = searchParams.get("sector") ?? "";
    setShowForm(true);
    setForm((prev) => ({
      ...prev,
      titulo: prev.titulo || (area ? `Evaluación EIIAX — ${area}` : "Evaluación EIIAX"),
      area_proceso: prev.area_proceso || area,
      necesidad: prev.necesidad || (temas ? `Interés confirmado durante demostración: ${area}. Temas: ${temas}.` : area ? `Interés confirmado durante demostración: ${area}.` : ""),
      objetivo: prev.objetivo || "Evaluar con información real de la entidad los temas priorizados durante la demostración y cuantificar oportunidades con evidencia.",
      sector: prev.sector || sector,
    }));
  }, [searchParams]);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    try {
      const created = await createEvaluacion(form);
      await syncInformacionExpediente(created.id);
      if (searchParams.get("nuevo") === "1") {
        const ext = await createEntidadExterna(created.id);
        const entidad = ext.entidad as Record<string, unknown> | undefined;
        if (entidad?.id) {
          const detail = await fetchEntidadExterna(String(entidad.id));
          const publicaciones = (detail.publicaciones as Record<string, unknown>[] | undefined) ?? [];
          for (const pub of publicaciones.filter((x) => ["INICIO", "INFORMACION"].includes(String(x.paquete)))) {
            if (String(pub.estado) !== "PUBLICADO_EMPRESA") {
              await setPublicacionEstado(String(pub.id), "PUBLICADO_EMPRESA", undefined, "Preparado automáticamente desde cierre de demostración");
            }
          }
        }
        window.location.href = `/centro-control?expediente=${created.id}&seccion=espacio_externo`;
        return;
      }
      window.location.href = `/evaluaciones/${created.id}?tab=informacion`;
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
                <th>Acciones</th>
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
                  <td className="actions-cell compact-actions">
                    <Link to={`/evaluaciones/${item.id}`} className="btn small primary">Cabina</Link>
                    <Link to={`/centro-control?expediente=${item.id}`} className="btn small secondary">Centro</Link>
                  </td>
                </tr>
              ))}
              {!items.length && (
                <tr><td colSpan={8} className="muted">Sin expedientes. Cree una evaluación para comenzar.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
