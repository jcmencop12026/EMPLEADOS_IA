import { useCallback, useEffect, useState } from "react";
import {
  ApiError,
  createPlatformOrganization,
  fetchPlatformOrganizations,
  setPlatformOrganizationStatus,
  type PlatformOrganization,
} from "../../api";
import { EmptyState, ErrorState, LoadingState } from "../../components/AsyncState";
import { getCachedUser } from "../../auth/session";

const STATUS_LABEL: Record<string, string> = {
  ACTIVE: "Activa",
  INACTIVE: "Inactiva",
};

export function AdminCompaniesPage() {
  const user = getCachedUser();
  const canManage = user?.permissions?.includes("platform.organization.manage");
  const [companies, setCompanies] = useState<PlatformOrganization[]>([]);
  const [q, setQ] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [tempPassword, setTempPassword] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: "",
    slug: "",
    timezone: "America/Bogota",
    admin_username: "",
    admin_password: "",
    admin_email: "",
    admin_full_name: "",
  });

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchPlatformOrganizations()
      .then(setCompanies)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Error al cargar empresas"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  function slugFromName(name: string): string {
    return name
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 60);
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setTempPassword(null);
    try {
      const res = await createPlatformOrganization({
        name: form.name,
        slug: form.slug,
        timezone: form.timezone,
        admin_username: form.admin_username,
        admin_password: form.admin_password || undefined,
        admin_email: form.admin_email || undefined,
        admin_full_name: form.admin_full_name || undefined,
      });
      setShowForm(false);
      setForm({
        name: "",
        slug: "",
        timezone: "America/Bogota",
        admin_username: "",
        admin_password: "",
        admin_email: "",
        admin_full_name: "",
      });
      if (res.temporary_password) setTempPassword(res.temporary_password);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo crear la empresa");
    } finally {
      setSaving(false);
    }
  }

  async function toggleStatus(org: PlatformOrganization) {
    const next = org.status === "ACTIVE" ? "INACTIVE" : "ACTIVE";
    const label = next === "INACTIVE" ? "desactivar" : "activar";
    if (!window.confirm(`¿Confirma ${label} la empresa «${org.name}»?`)) return;
    try {
      await setPlatformOrganizationStatus(org.id, next);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo cambiar el estado");
    }
  }

  const filtered = companies.filter((c) => {
    const term = q.trim().toLowerCase();
    if (!term) return true;
    return c.name.toLowerCase().includes(term) || c.slug.toLowerCase().includes(term);
  });

  if (loading) return <LoadingState message="Cargando empresas…" />;
  if (error && companies.length === 0) return <ErrorState message={error} onRetry={load} />;

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Empresas</h1>
        <p className="muted">Administración multiempresa de la plataforma</p>
      </header>

      <div className="ops-toolbar">
        <input
          type="search"
          placeholder="Buscar por nombre o identificador…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <button type="button" className="btn primary" onClick={() => setShowForm((v) => !v)}>
          {showForm ? "Cancelar" : "Nueva empresa"}
        </button>
      </div>

      {tempPassword && (
        <p className="panel muted">
          Contraseña temporal del administrador: <span className="mono">{tempPassword}</span>
        </p>
      )}

      {showForm && (
        <form className="panel" onSubmit={handleCreate}>
          <h2>Crear empresa</h2>
          <label>Nombre *
            <input
              required
              value={form.name}
              onChange={(e) => {
                const name = e.target.value;
                setForm((f) => ({ ...f, name, slug: f.slug || slugFromName(name) }));
              }}
            />
          </label>
          <label>Identificador (slug) *
            <input
              required
              pattern="[a-z][a-z0-9-]+"
              value={form.slug}
              onChange={(e) => setForm((f) => ({ ...f, slug: e.target.value.toLowerCase() }))}
              placeholder="mi-empresa"
            />
          </label>
          <label>Zona horaria
            <input value={form.timezone} onChange={(e) => setForm((f) => ({ ...f, timezone: e.target.value }))} />
          </label>
          <label>Usuario administrador *
            <input required value={form.admin_username} onChange={(e) => setForm((f) => ({ ...f, admin_username: e.target.value }))} />
          </label>
          <label>Contraseña administrador
            <input
              type="password"
              value={form.admin_password}
              onChange={(e) => setForm((f) => ({ ...f, admin_password: e.target.value }))}
              placeholder="Opcional — se genera automáticamente"
            />
          </label>
          <label>Correo administrador
            <input type="email" value={form.admin_email} onChange={(e) => setForm((f) => ({ ...f, admin_email: e.target.value }))} />
          </label>
          <label>Nombre completo administrador
            <input value={form.admin_full_name} onChange={(e) => setForm((f) => ({ ...f, admin_full_name: e.target.value }))} />
          </label>
          <div className="ops-actions">
            <button type="submit" className="btn primary" disabled={saving}>{saving ? "Creando…" : "Crear empresa"}</button>
          </div>
        </form>
      )}

      {error && <p className="error">{error}</p>}

      {filtered.length === 0 ? (
        <EmptyState title="Sin empresas" message="No hay empresas que coincidan con la búsqueda." />
      ) : (
        <div className="panel table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Identificador</th>
                <th>Estado</th>
                <th>Usuarios</th>
                <th>Creada</th>
                {canManage && <th>Acciones</th>}
              </tr>
            </thead>
            <tbody>
              {filtered.map((org) => (
                <tr key={org.id}>
                  <td>{org.name}</td>
                  <td className="mono">{org.slug}</td>
                  <td>{STATUS_LABEL[org.status] || org.status}</td>
                  <td>{org.users_count}</td>
                  <td>{new Date(org.created_at).toLocaleString()}</td>
                  {canManage && (
                    <td>
                      <button type="button" className="btn" onClick={() => toggleStatus(org)}>
                        {org.status === "ACTIVE" ? "Desactivar" : "Activar"}
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
