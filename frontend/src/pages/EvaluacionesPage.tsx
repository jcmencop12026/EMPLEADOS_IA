import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { createEvaluacion, fetchEvaluaciones, type EvaluacionExpedienteSummary } from "../api";
import { ContextualHelp } from "../components/ContextualHelp";
import { EiaaxTable, type EiaaxColumn } from "../components/EiaaxTable";
import { usePermissions } from "../hooks/usePermissions";
import {
  formatConfianza,
  formatPorcentaje,
  labelEstadoEvaluacion,
  labelNivelEvaluacion,
} from "../lib/evaluacionLabels";
import { HELP_EVALUACION_CREAR, HELP_EVALUACIONES_LISTA } from "../lib/evaluacionHelp";

const ESTADOS_FILTRO = [
  { value: "", label: "Todos los estados" },
  { value: "BORRADOR", label: "Borrador" },
  { value: "EN_CURSO", label: "En curso" },
  { value: "PRELIMINAR", label: "Preliminar" },
  { value: "DIAGNOSTICA", label: "Diagnóstica" },
  { value: "PROFUNDA", label: "Profunda" },
  { value: "CERRADO", label: "Cerrado" },
] as const;

export function EvaluacionesPage() {
  const { has } = usePermissions();
  const [searchParams] = useSearchParams();
  const [items, setItems] = useState<EvaluacionExpedienteSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filtroEstado, setFiltroEstado] = useState("");
  const nuevoFromDemo = searchParams.get("nuevo") === "1";
  const areaFromDemo = searchParams.get("area_label") || searchParams.get("area") || "";
  const [showForm, setShowForm] = useState(nuevoFromDemo);
  const [form, setForm] = useState({
    titulo: areaFromDemo ? `Evaluación — ${areaFromDemo}` : "",
    entidad_nombre: "",
    necesidad: "",
    objetivo: areaFromDemo ? `Evaluar oportunidades en ${areaFromDemo}` : "",
    area_proceso: areaFromDemo,
    nivel: "PRELIMINAR",
  });

  function load() {
    const params = new URLSearchParams();
    if (filtroEstado) params.set("estado", filtroEstado);
    setLoading(true);
    fetchEvaluaciones(params.toString())
      .then((r) => {
        setItems(r.items);
        setError(null);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar"))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
  }, [filtroEstado]);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    try {
      const created = await createEvaluacion(form);
      window.location.href = `/evaluaciones/${created.id}`;
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo crear la evaluación");
    }
  }

  const columns = useMemo<EiaaxColumn<EvaluacionExpedienteSummary>[]>(
    () => [
      {
        key: "codigo",
        label: "Código",
        sortable: true,
        getValue: (r) => r.codigo,
        render: (r) => <Link to={`/evaluaciones/${r.id}`}>{r.codigo}</Link>,
      },
      { key: "titulo", label: "Evaluación", sortable: true, getValue: (r) => r.titulo },
      { key: "entidad_nombre", label: "Entidad", sortable: true, getValue: (r) => r.entidad_nombre },
      {
        key: "estado",
        label: "Estado",
        sortable: true,
        getValue: (r) => r.estado,
        render: (r) => <span className="badge estado-eval">{labelEstadoEvaluacion(r.estado)}</span>,
      },
      {
        key: "porcentaje_informacion",
        label: "Info %",
        sortable: true,
        getValue: (r) => r.porcentaje_informacion,
        render: (r) => formatPorcentaje(r.porcentaje_informacion),
      },
      {
        key: "confianza_global",
        label: "Confianza",
        sortable: true,
        getValue: (r) => r.confianza_global,
        render: (r) => <span className="badge confianza">{formatConfianza(r.confianza_global)}</span>,
      },
      {
        key: "nivel",
        label: "Nivel",
        sortable: true,
        getValue: (r) => r.nivel,
        render: (r) => labelNivelEvaluacion(r.nivel),
      },
    ],
    [],
  );

  return (
    <div className="ops-page">
      <header className="page-header">
        <div className="page-header-row">
          <div>
            <h1>Evaluaciones EIAAX</h1>
            <p className="muted">Expedientes de evaluación empresarial — entidad, información, análisis e impacto</p>
          </div>
          <ContextualHelp content={HELP_EVALUACIONES_LISTA} />
        </div>
      </header>

      {nuevoFromDemo && (
        <p className="panel muted-box">
          Flujo real de evaluación — complete los datos de su organización. La demo ficticia permanece en{" "}
          <Link to="/demo">Demo comercial</Link>.
        </p>
      )}

      {error && <p className="error">{error}</p>}

      <div className="panel compact-panel filters-row">
        <select value={filtroEstado} onChange={(e) => setFiltroEstado(e.target.value)} aria-label="Filtrar por estado">
          {ESTADOS_FILTRO.map((s) => (
            <option key={s.value || "all"} value={s.value}>
              {s.label}
            </option>
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
          <div className="page-header-row">
            <h2>Nueva evaluación</h2>
            <ContextualHelp content={HELP_EVALUACION_CREAR} />
          </div>
          <div className="form-grid">
            <label>
              Título
              <input required value={form.titulo} onChange={(e) => setForm({ ...form, titulo: e.target.value })} />
            </label>
            <label>
              Entidad
              <input
                required
                value={form.entidad_nombre}
                onChange={(e) => setForm({ ...form, entidad_nombre: e.target.value })}
              />
            </label>
            <label>
              Área/proceso
              <input value={form.area_proceso} onChange={(e) => setForm({ ...form, area_proceso: e.target.value })} />
            </label>
            <label>
              Nivel
              <select value={form.nivel} onChange={(e) => setForm({ ...form, nivel: e.target.value })}>
                <option value="PRELIMINAR">Preliminar</option>
                <option value="DIAGNOSTICA">Diagnóstica</option>
                <option value="PROFUNDA">Profunda</option>
              </select>
            </label>
          </div>
          <label>
            Problema / necesidad
            <textarea rows={2} value={form.necesidad} onChange={(e) => setForm({ ...form, necesidad: e.target.value })} />
          </label>
          <label>
            Objetivo
            <textarea rows={2} value={form.objetivo} onChange={(e) => setForm({ ...form, objetivo: e.target.value })} />
          </label>
          <button type="submit" className="btn primary">
            Crear expediente
          </button>
        </form>
      )}

      <div className="panel compact-panel">
        <EiaaxTable
          columns={columns}
          data={items}
          rowKey={(r) => r.id}
          loading={loading}
          prefsKey="evaluaciones_lista_v1"
          searchPlaceholder="Buscar por código, título o entidad…"
          searchKeys={["codigo", "titulo", "entidad_nombre"]}
          emptyMessage="Sin expedientes. Cree una evaluación para comenzar."
          defaultSortKey="codigo"
          defaultSortDir="desc"
        />
      </div>
    </div>
  );
}
