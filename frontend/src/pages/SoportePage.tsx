import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { SupportCase } from "../api";
import { createSupportCase, fetchSupportCases, fetchSupportTipos } from "../api";
import { usePermissions } from "../hooks/usePermissions";

export function SoportePage() {
  const { has } = usePermissions();
  const [cases, setCases] = useState<SupportCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [estado, setEstado] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [tipos, setTipos] = useState<string[]>([]);
  const [form, setForm] = useState({
    tipo: "SOLICITUD",
    asunto: "",
    descripcion: "",
    prioridad: "MEDIA",
    impacto: "MEDIO",
    urgencia: "MEDIA",
  });

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchSupportCases({ q: q || undefined, estado: estado || undefined, solo_mios: !has("support.view") })
      .then(setCases)
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar casos"))
      .finally(() => setLoading(false));
  }, [q, estado, has]);

  useEffect(() => {
    load();
    fetchSupportTipos().then((t) => setTipos(t.tipos)).catch(() => undefined);
  }, [load]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    try {
      await createSupportCase(form);
      setShowForm(false);
      setForm({ tipo: "SOLICITUD", asunto: "", descripcion: "", prioridad: "MEDIA", impacto: "MEDIO", urgencia: "MEDIA" });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo crear el caso");
    }
  }

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Mesa de Ayuda y Soporte</h1>
        <p className="muted">Gestión de solicitudes e incidentes de su organización</p>
      </header>

      <div className="toolbar compact-toolbar">
        <input
          type="search"
          placeholder="Buscar…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          aria-label="Buscar casos"
        />
        <select value={estado} onChange={(e) => setEstado(e.target.value)} aria-label="Filtrar por estado">
          <option value="">Todos los estados</option>
          <option value="NUEVO">Nuevo</option>
          <option value="ASIGNADO">Asignado</option>
          <option value="EN_PROCESO">En proceso</option>
          <option value="PENDIENTE_USUARIO">Pendiente usuario</option>
          <option value="RESUELTO">Resuelto</option>
          <option value="CERRADO">Cerrado</option>
        </select>
        <button type="button" onClick={load}>Actualizar</button>
        {has("support.create") && (
          <button type="button" className="btn primary" onClick={() => setShowForm(!showForm)}>
            {showForm ? "Cancelar" : "Nuevo caso"}
          </button>
        )}
      </div>

      {error && <p className="error">{error}</p>}

      {showForm && has("support.create") && (
        <form className="panel" onSubmit={handleCreate}>
          <h2>Nuevo caso</h2>
          <label>
            Tipo
            <select value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value })}>
              {tipos.map((t) => (
                <option key={t} value={t}>{t.replace(/_/g, " ")}</option>
              ))}
            </select>
          </label>
          <label>
            Asunto
            <input required value={form.asunto} onChange={(e) => setForm({ ...form, asunto: e.target.value })} />
          </label>
          <label>
            Descripción
            <textarea required rows={4} value={form.descripcion} onChange={(e) => setForm({ ...form, descripcion: e.target.value })} />
          </label>
          <label>
            Prioridad
            <select value={form.prioridad} onChange={(e) => setForm({ ...form, prioridad: e.target.value })}>
              <option value="CRITICA">Crítica</option>
              <option value="ALTA">Alta</option>
              <option value="MEDIA">Media</option>
              <option value="BAJA">Baja</option>
            </select>
          </label>
          <button type="submit" className="btn primary">Crear caso</button>
        </form>
      )}

      {loading ? (
        <p className="muted">Cargando casos…</p>
      ) : (
        <table className="data-table compact-table">
          <thead>
            <tr>
              <th>Referencia</th>
              <th>Tipo</th>
              <th>Asunto</th>
              <th>Estado</th>
              <th>Prioridad</th>
              <th>SLA</th>
              <th>Actualizado</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {cases.length === 0 ? (
              <tr><td colSpan={8} className="muted">No hay casos.</td></tr>
            ) : (
              cases.map((c) => (
                <tr key={c.id}>
                  <td className="mono">{c.referencia}</td>
                  <td>{c.tipo}</td>
                  <td>{c.asunto}</td>
                  <td>{c.estado}</td>
                  <td>{c.prioridad}</td>
                  <td>
                    <span className={`cc-tag cc-tag-${c.sla_estado === "VENCIDO" ? "inferencia" : c.sla_estado === "PROXIMO" ? "recomendacion" : "hecho"}`}>
                      {c.sla_estado ?? "—"}
                    </span>
                  </td>
                  <td>{c.updated_at ? new Date(c.updated_at).toLocaleString() : "—"}</td>
                  <td><Link to={`/soporte/casos/${c.id}`}>Ver</Link></td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}
