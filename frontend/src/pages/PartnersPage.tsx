import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { createPartner, fetchPartners, type PartnerSummary } from "../api";
import { usePermissions } from "../hooks/usePermissions";

const ESTADOS = ["", "BORRADOR", "ACTIVO", "INACTIVO", "SUSPENDIDO"] as const;

export function PartnersPage() {
  const { has } = usePermissions();
  const [items, setItems] = useState<PartnerSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busqueda, setBusqueda] = useState("");
  const [filtroEstado, setFiltroEstado] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    nombre: "",
    razon_social: "",
    tipo_relacion: "CONSULTOR",
    contacto_nombre: "",
    contacto_email: "",
    contacto_telefono: "",
    alcance_descripcion: "",
  });

  function load() {
    const params = new URLSearchParams();
    if (busqueda) params.set("q", busqueda);
    if (filtroEstado) params.set("estado", filtroEstado);
    setLoading(true);
    fetchPartners(params.toString())
      .then((r) => { setItems(r.items); setTotal(r.total); setError(null); })
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar"))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, [busqueda, filtroEstado]);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    try {
      const created = await createPartner(form);
      window.location.href = `/partners/${created.id}`;
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo crear el partner");
    }
  }

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Partners y aliados</h1>
        <p className="muted">Gestión comercial MB-03 — acceso explícito a organizaciones autorizadas</p>
      </header>

      {error && <p className="error">{error}</p>}

      <div className="panel compact-panel filters-row">
        <input
          type="search"
          placeholder="Buscar por código o nombre…"
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
        />
        <select value={filtroEstado} onChange={(e) => setFiltroEstado(e.target.value)}>
          {ESTADOS.map((s) => (
            <option key={s || "all"} value={s}>{s || "Todos los estados"}</option>
          ))}
        </select>
        {has("partners.manage") && (
          <button type="button" className="btn primary" onClick={() => setShowForm((v) => !v)}>
            {showForm ? "Cancelar" : "Nuevo partner"}
          </button>
        )}
      </div>

      {showForm && has("partners.manage") && (
        <form className="panel compact-panel eval-create-form" onSubmit={onCreate}>
          <h2>Nuevo partner</h2>
          <div className="form-grid">
            <label>Nombre<input required value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} /></label>
            <label>Razón social<input value={form.razon_social} onChange={(e) => setForm({ ...form, razon_social: e.target.value })} /></label>
            <label>Tipo relación
              <select value={form.tipo_relacion} onChange={(e) => setForm({ ...form, tipo_relacion: e.target.value })}>
                <option value="CONSULTOR">Consultor</option>
                <option value="INTEGRADOR">Integrador</option>
                <option value="DISTRIBUIDOR">Distribuidor</option>
                <option value="ALIADO_ESTRATEGICO">Aliado estratégico</option>
              </select>
            </label>
            <label>Contacto<input value={form.contacto_nombre} onChange={(e) => setForm({ ...form, contacto_nombre: e.target.value })} /></label>
            <label>Email<input type="email" value={form.contacto_email} onChange={(e) => setForm({ ...form, contacto_email: e.target.value })} /></label>
            <label>Teléfono<input value={form.contacto_telefono} onChange={(e) => setForm({ ...form, contacto_telefono: e.target.value })} /></label>
          </div>
          <label>Alcance comercial<textarea rows={2} value={form.alcance_descripcion} onChange={(e) => setForm({ ...form, alcance_descripcion: e.target.value })} /></label>
          <button type="submit" className="btn primary">Crear partner</button>
        </form>
      )}

      {loading ? <p className="muted">Cargando…</p> : (
        <div className="panel compact-panel">
          <p className="muted">{total} partner(s)</p>
          <table className="data-table compact-table">
            <thead>
              <tr>
                <th>Código</th>
                <th>Nombre</th>
                <th>Estado</th>
                <th>Tipo</th>
                <th>Contacto</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td><Link to={`/partners/${item.id}`}>{item.codigo}</Link></td>
                  <td>{item.nombre}</td>
                  <td><span className={`badge estado-${item.estado.toLowerCase()}`}>{item.estado}</span></td>
                  <td>{item.tipo_relacion}</td>
                  <td>{item.contacto_email || item.contacto_nombre || "—"}</td>
                </tr>
              ))}
              {!items.length && (
                <tr><td colSpan={5} className="muted">Sin partners. Cree uno para comenzar.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
