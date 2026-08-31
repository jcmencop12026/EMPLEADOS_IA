import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  assignPartnerUser,
  fetchPartner,
  fetchPartnerAuditoria,
  fetchPartnerCatalogo,
  fetchPlatformOrganizations,
  grantPartnerOrganization,
  revokePartnerGrant,
  revokePartnerUser,
  setPartnerEstado,
  updatePartnerGrantAlcance,
  type PartnerDetail,
  type PartnerGrant,
  type PartnerMembership,
  type PlatformOrganization,
} from "../api";
import { usePermissions } from "../hooks/usePermissions";

type Tab = "detalle" | "organizaciones" | "usuarios" | "alcance" | "actividad";

const TABS: { id: Tab; label: string }[] = [
  { id: "detalle", label: "Detalle" },
  { id: "organizaciones", label: "Organizaciones" },
  { id: "usuarios", label: "Usuarios" },
  { id: "alcance", label: "Alcance" },
  { id: "actividad", label: "Actividad" },
];

const ALCANCE_LABELS: Record<string, string> = {
  "organizacion.read": "Lectura organización",
  "cc.view": "Centro de control",
  "trabajo.view": "Mi trabajo",
  "evaluacion.view": "Evaluaciones",
  "oportunidades.view": "Oportunidades",
};

export function PartnerDetailPage() {
  const { partnerId } = useParams<{ partnerId: string }>();
  const { has } = usePermissions();
  const [tab, setTab] = useState<Tab>("detalle");
  const [partner, setPartner] = useState<PartnerDetail | null>(null);
  const [auditoria, setAuditoria] = useState<Array<Record<string, unknown>>>([]);
  const [orgs, setOrgs] = useState<PlatformOrganization[]>([]);
  const [alcances, setAlcances] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [grantOrgId, setGrantOrgId] = useState("");
  const [grantAlcance, setGrantAlcance] = useState<string[]>(["organizacion.read"]);
  const [assignUserId, setAssignUserId] = useState("");
  const [assignRol, setAssignRol] = useState("OPERADOR");

  const load = useCallback(() => {
    if (!partnerId) return;
    setLoading(true);
    fetchPartner(partnerId)
      .then((data) => { setPartner(data); setError(null); })
      .catch((e) => setError(e instanceof Error ? e.message : "Error"))
      .finally(() => setLoading(false));
  }, [partnerId]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    if (!partnerId) return;
    if (tab === "actividad") {
      fetchPartnerAuditoria(partnerId).then((r) => setAuditoria(r.items)).catch(() => undefined);
    }
    if (tab === "organizaciones" && has("platform.organization.view")) {
      fetchPlatformOrganizations().then(setOrgs).catch(() => undefined);
    }
    if (tab === "alcance" || tab === "organizaciones") {
      fetchPartnerCatalogo().then((c) => setAlcances(c.alcances)).catch(() => undefined);
    }
  }, [tab, partnerId, has]);

  async function onActivar() {
    if (!partnerId) return;
    await setPartnerEstado(partnerId, "ACTIVO");
    setMsg("Partner activado");
    load();
  }

  async function onDesactivar() {
    if (!partnerId) return;
    await setPartnerEstado(partnerId, "INACTIVO");
    setMsg("Partner desactivado");
    load();
  }

  async function onGrantOrg(e: FormEvent) {
    e.preventDefault();
    if (!partnerId || !grantOrgId) return;
    try {
      await grantPartnerOrganization(partnerId, { organization_id: grantOrgId, alcance: grantAlcance });
      setMsg("Organización asociada");
      setGrantOrgId("");
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al asociar");
    }
  }

  async function onRevokeGrant(g: PartnerGrant) {
    if (!partnerId) return;
    await revokePartnerGrant(partnerId, g.id);
    setMsg("Acceso revocado");
    load();
  }

  async function onAssignUser(e: FormEvent) {
    e.preventDefault();
    if (!partnerId || !assignUserId) return;
    try {
      await assignPartnerUser(partnerId, { user_id: assignUserId, rol: assignRol });
      setMsg("Usuario asignado");
      setAssignUserId("");
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al asignar");
    }
  }

  async function onRevokeUser(m: PartnerMembership) {
    if (!partnerId) return;
    await revokePartnerUser(partnerId, m.id);
    setMsg("Usuario revocado");
    load();
  }

  async function onUpdateAlcance(g: PartnerGrant, nuevo: string[]) {
    if (!partnerId) return;
    await updatePartnerGrantAlcance(partnerId, g.id, nuevo);
    setMsg("Alcance actualizado");
    load();
  }

  function toggleAlcance(code: string) {
    setGrantAlcance((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code],
    );
  }

  if (!partnerId) return <p className="error">Partner no especificado</p>;
  if (loading && !partner) return <p className="muted">Cargando…</p>;
  if (!partner) return <p className="error">{error || "Partner no encontrado"}</p>;

  const canManage = has("partners.manage");
  const canGrant = canManage || has("partners.org.grant");
  const canAssign = canManage || has("partners.user.assign");

  return (
    <div className="ops-page">
      <header className="page-header">
        <div>
          <Link to="/partners" className="muted">← Partners</Link>
          <h1>{partner.nombre}</h1>
          <p className="muted">{partner.codigo} · {partner.estado} · {partner.tipo_relacion}</p>
        </div>
        {canManage && (
          <div className="header-actions">
            {partner.estado !== "ACTIVO" && (
              <button type="button" className="btn primary" onClick={onActivar}>Activar</button>
            )}
            {partner.estado === "ACTIVO" && (
              <button type="button" className="btn" onClick={onDesactivar}>Desactivar</button>
            )}
          </div>
        )}
      </header>

      {error && <p className="error">{error}</p>}
      {msg && <p className="success-msg">{msg}</p>}

      <nav className="tab-nav compact-tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            className={tab === t.id ? "tab active" : "tab"}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {tab === "detalle" && (
        <div className="panel compact-panel">
          <dl className="detail-grid">
            <dt>Razón social</dt><dd>{partner.razon_social || "—"}</dd>
            <dt>Contacto</dt><dd>{partner.contacto_nombre || "—"}</dd>
            <dt>Email</dt><dd>{partner.contacto_email || "—"}</dd>
            <dt>Teléfono</dt><dd>{partner.contacto_telefono || "—"}</dd>
            <dt>Alcance comercial</dt><dd>{partner.alcance_descripcion || "—"}</dd>
            <dt>Vigencia</dt>
            <dd>
              {partner.valid_from || partner.valid_until
                ? `${partner.valid_from || "—"} → ${partner.valid_until || "—"}`
                : "Sin límite"}
            </dd>
          </dl>
        </div>
      )}

      {tab === "organizaciones" && (
        <div className="panel compact-panel">
          {canGrant && has("platform.organization.view") && (
            <form className="inline-form" onSubmit={onGrantOrg}>
              <select required value={grantOrgId} onChange={(e) => setGrantOrgId(e.target.value)}>
                <option value="">Seleccionar organización…</option>
                {orgs.map((o) => (
                  <option key={o.id} value={o.id}>{o.name}</option>
                ))}
              </select>
              <div className="alcance-checks">
                {alcances.map((code) => (
                  <label key={code} className="checkbox-inline">
                    <input
                      type="checkbox"
                      checked={grantAlcance.includes(code)}
                      onChange={() => toggleAlcance(code)}
                    />
                    {ALCANCE_LABELS[code] || code}
                  </label>
                ))}
              </div>
              <button type="submit" className="btn primary">Asociar organización</button>
            </form>
          )}
          <table className="data-table compact-table">
            <thead>
              <tr>
                <th>Organización</th>
                <th>Estado</th>
                <th>Alcance</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {partner.organizaciones.map((g) => (
                <tr key={g.id}>
                  <td>{g.organization_name || g.organization_id}</td>
                  <td>{g.estado}</td>
                  <td>{g.alcance.map((a) => ALCANCE_LABELS[a] || a).join(", ")}</td>
                  <td>
                    {canGrant && g.estado === "ACTIVO" && (
                      <button type="button" className="btn btn-sm" onClick={() => onRevokeGrant(g)}>
                        Revocar
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {!partner.organizaciones.length && (
                <tr><td colSpan={4} className="muted">Sin organizaciones asociadas.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {tab === "usuarios" && (
        <div className="panel compact-panel">
          {canAssign && (
            <form className="inline-form" onSubmit={onAssignUser}>
              <input
                placeholder="ID de usuario"
                value={assignUserId}
                onChange={(e) => setAssignUserId(e.target.value)}
                required
              />
              <select value={assignRol} onChange={(e) => setAssignRol(e.target.value)}>
                <option value="ADMIN">Administrador</option>
                <option value="OPERADOR">Operador</option>
                <option value="LECTOR">Lector</option>
              </select>
              <button type="submit" className="btn primary">Asignar usuario</button>
            </form>
          )}
          <table className="data-table compact-table">
            <thead>
              <tr><th>Usuario</th><th>Nombre</th><th>Rol</th><th>Estado</th><th>Acciones</th></tr>
            </thead>
            <tbody>
              {partner.usuarios.map((m) => (
                <tr key={m.id}>
                  <td>{m.username || m.user_id}</td>
                  <td>{m.full_name || "—"}</td>
                  <td>{m.rol}</td>
                  <td>{m.is_active ? "Activo" : "Revocado"}</td>
                  <td>
                    {canAssign && m.is_active && (
                      <button type="button" className="btn btn-sm" onClick={() => onRevokeUser(m)}>
                        Revocar
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {!partner.usuarios.length && (
                <tr><td colSpan={5} className="muted">Sin usuarios asignados.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {tab === "alcance" && (
        <div className="panel compact-panel">
          <p className="muted">Alcance por organización — permisos explícitos y revocables</p>
          {partner.organizaciones.filter((g) => g.estado === "ACTIVO").map((g) => (
            <div key={g.id} className="alcance-block">
              <h3>{g.organization_name || g.organization_id}</h3>
              <div className="alcance-checks">
                {alcances.map((code) => (
                  <label key={code} className="checkbox-inline">
                    <input
                      type="checkbox"
                      checked={g.alcance.includes(code)}
                      disabled={!canGrant}
                      onChange={() => {
                        const nuevo = g.alcance.includes(code)
                          ? g.alcance.filter((c) => c !== code)
                          : [...g.alcance, code];
                        if (nuevo.length) onUpdateAlcance(g, nuevo);
                      }}
                    />
                    {ALCANCE_LABELS[code] || code}
                  </label>
                ))}
              </div>
            </div>
          ))}
          {!partner.organizaciones.filter((g) => g.estado === "ACTIVO").length && (
            <p className="muted">Asocie organizaciones para configurar alcance.</p>
          )}
        </div>
      )}

      {tab === "actividad" && (
        <div className="panel compact-panel">
          <table className="data-table compact-table">
            <thead>
              <tr><th>Fecha</th><th>Acción</th><th>Detalle</th></tr>
            </thead>
            <tbody>
              {auditoria.map((e) => (
                <tr key={String(e.id)}>
                  <td>{String(e.created_at || "")}</td>
                  <td>{String(e.action || "")}</td>
                  <td><code>{JSON.stringify(e.detail)}</code></td>
                </tr>
              ))}
              {!auditoria.length && (
                <tr><td colSpan={3} className="muted">Sin eventos registrados.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
