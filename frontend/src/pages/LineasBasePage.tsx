import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { LineaBaseItem } from "../api";
import { createLineaBase, fetchLineasBase } from "../api";
import { usePermissions } from "../hooks/usePermissions";

const ESTADOS = ["", "BORRADOR", "ACTIVA", "EN_MEDICION", "VALIDADA", "CERRADA"] as const;

const ESTADO_LABELS: Record<string, string> = {
  BORRADOR: "Borrador",
  ACTIVA: "Activa",
  EN_MEDICION: "En medición",
  VALIDADA: "Validada",
  CERRADA: "Cerrada",
};

const DIRECCION_LABELS: Record<string, string> = {
  MAYOR_ES_MEJOR: "Mayor es mejor",
  MENOR_ES_MEJOR: "Menor es mejor",
  INFORMATIVO: "Informativo",
};

export function LineasBasePage() {
  const { has } = usePermissions();
  const [items, setItems] = useState<LineaBaseItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [filtroEstado, setFiltroEstado] = useState("");
  const [busqueda, setBusqueda] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    indicador: "",
    descripcion: "",
    unidad: "unidad",
    valor_base: "",
    fecha_inicio_base: "",
    fecha_fin_base: "",
    direccion_indicador: "MAYOR_ES_MEJOR",
    impacto_esperado: "",
    estado: "BORRADOR",
  });

  useEffect(() => {
    const params = new URLSearchParams();
    if (filtroEstado) params.set("estado", filtroEstado);
    if (busqueda) params.set("indicador", busqueda);
    setLoading(true);
    fetchLineasBase(params.toString())
      .then((res) => {
        setItems(res.items);
        setError(null);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar"))
      .finally(() => setLoading(false));
  }, [filtroEstado, busqueda]);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    if (!form.indicador || !form.valor_base) return;
    try {
      const created = await createLineaBase({
        indicador: form.indicador,
        descripcion: form.descripcion || undefined,
        unidad: form.unidad,
        valor_base: Number(form.valor_base),
        fecha_inicio_base: new Date(form.fecha_inicio_base).toISOString(),
        fecha_fin_base: new Date(form.fecha_fin_base).toISOString(),
        direccion_indicador: form.direccion_indicador,
        impacto_esperado: form.impacto_esperado ? Number(form.impacto_esperado) : undefined,
        estado: form.estado,
      });
      setMsg("Línea base creada");
      setShowForm(false);
      setItems((prev) => [created, ...prev]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al crear");
    }
  }

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Líneas base e impacto</h1>
        <p className="muted">Medición antes/después de intervenciones y acciones</p>
      </header>

      {error && <p className="error">{error}</p>}
      {msg && <p className="success">{msg}</p>}
      {loading && <p className="muted">Cargando líneas base…</p>}

      <div className="panel">
        <div className="toolbar compact-toolbar">
          <input
            type="search"
            placeholder="Buscar indicador…"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
          />
          <select value={filtroEstado} onChange={(e) => setFiltroEstado(e.target.value)}>
            <option value="">Todos los estados</option>
            {ESTADOS.filter(Boolean).map((e) => (
              <option key={e} value={e}>{ESTADO_LABELS[e] ?? e}</option>
            ))}
          </select>
          {has("linea_base.manage") && (
            <button type="button" onClick={() => setShowForm((v) => !v)}>
              {showForm ? "Cancelar" : "Nueva línea base"}
            </button>
          )}
        </div>

        {showForm && has("linea_base.manage") && (
          <form className="compact-form" onSubmit={onCreate}>
            <h3 className="section-title">Crear línea base</h3>
            <label>Indicador<input value={form.indicador} onChange={(e) => setForm({ ...form, indicador: e.target.value })} required /></label>
            <label>Descripción<input value={form.descripcion} onChange={(e) => setForm({ ...form, descripcion: e.target.value })} /></label>
            <label>Unidad<input value={form.unidad} onChange={(e) => setForm({ ...form, unidad: e.target.value })} /></label>
            <label>Valor base<input type="number" value={form.valor_base} onChange={(e) => setForm({ ...form, valor_base: e.target.value })} required /></label>
            <label>Inicio periodo base<input type="date" value={form.fecha_inicio_base} onChange={(e) => setForm({ ...form, fecha_inicio_base: e.target.value })} required /></label>
            <label>Fin periodo base<input type="date" value={form.fecha_fin_base} onChange={(e) => setForm({ ...form, fecha_fin_base: e.target.value })} required /></label>
            <label>
              Dirección del indicador
              <select value={form.direccion_indicador} onChange={(e) => setForm({ ...form, direccion_indicador: e.target.value })}>
                <option value="MAYOR_ES_MEJOR">Mayor es mejor</option>
                <option value="MENOR_ES_MEJOR">Menor es mejor</option>
                <option value="INFORMATIVO">Informativo</option>
              </select>
            </label>
            <label>Impacto esperado (opcional)<input type="number" value={form.impacto_esperado} onChange={(e) => setForm({ ...form, impacto_esperado: e.target.value })} /></label>
            <button type="submit">Guardar línea base</button>
          </form>
        )}

        <div className="table-wrap">
          <table className="data-table compact-table">
            <thead>
              <tr>
                <th>Indicador</th>
                <th>Valor base</th>
                <th>Unidad</th>
                <th>Dirección</th>
                <th>Estado</th>
                <th>Impacto esperado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 && (
                <tr><td colSpan={7} className="muted">No hay líneas base registradas</td></tr>
              )}
              {items.map((item) => (
                <tr key={item.id}>
                  <td>{item.indicador}</td>
                  <td>{item.valor_base}</td>
                  <td>{item.unidad}</td>
                  <td>{DIRECCION_LABELS[item.direccion_indicador] ?? item.direccion_indicador}</td>
                  <td>{ESTADO_LABELS[item.estado] ?? item.estado}</td>
                  <td>{item.impacto_esperado ?? "—"}</td>
                  <td><Link to={`/lineas-base/${item.id}`}>Detalle</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
