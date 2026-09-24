import { FormEvent, useCallback, useEffect, useState } from "react";
import {
  createEntidadExterna,
  fetchEntidadExterna,
  inviteAccesoExterno,
  listEntidadesExternas,
  promoverEntidadCliente,
  setPublicacionEstado,
} from "../../api";
import { labelEstadoPublicacion, labelEstadoRelacion } from "../../lib/evaluacionLabels";

type Props = { expedienteId: string };

export function EspacioExternoAdminPanel({ expedienteId }: Props) {
  const [entidadId, setEntidadId] = useState<string | null>(null);
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);
  const [publicacionObs, setPublicacionObs] = useState("");
  const [contratoRef, setContratoRef] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [inviteStatus, setInviteStatus] = useState<"idle" | "sending" | "sent" | "failed">("idle");

  const load = useCallback(() => {
    if (!entidadId) return;
    fetchEntidadExterna(entidadId).then(setDetail).catch(() => undefined);
  }, [entidadId]);

  useEffect(() => {
    listEntidadesExternas(expedienteId)
      .then((items) => {
        const first = items[0] as Record<string, unknown> | undefined;
        if (first?.id) {
          setEntidadId(String(first.id));
        }
      })
      .catch(() => undefined);
  }, [expedienteId]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    const entidad = detail?.entidad as Record<string, unknown> | undefined;
    if (entidad?.contrato_ref) {
      setContratoRef(String(entidad.contrato_ref));
    }
  }, [detail]);

  async function onCrearEntidad() {
    try {
      const r = await createEntidadExterna(expedienteId);
      const ent = r.entidad as Record<string, unknown>;
      setEntidadId(String(ent.id));
      setDetail(r);
      setMsg("Entidad externa vinculada");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    }
  }

  async function onInvite(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!entidadId) return;
    const form = e.currentTarget;
    const fd = new FormData(form);
    try {
      setInviteStatus("sending");
      const result = await inviteAccesoExterno(entidadId, {
        email: String(fd.get("email")),
        full_name: String(fd.get("full_name")),
      });
      const correoEstado = String(result.correo_estado ?? "NO_CONFIGURADO");
      if (correoEstado === "ENVIADA") {
        setMsg("Invitación enviada. El contacto creará su propia contraseña desde el enlace seguro recibido por correo.");
        setInviteStatus("sent");
        setError(null);
      } else {
        setMsg("Acceso externo creado correctamente.");
        setInviteStatus("failed");
        setError(correoEstado === "FALLIDA"
          ? "El acceso quedó preparado, pero el correo no pudo enviarse. Corrija el canal y reintente; EIIAX no entrega contraseñas temporales."
          : "No hay un canal de correo configurado. El acceso quedó activo; complete la configuración del canal y reintente la invitación.");
      }
      load();
      form.reset();
    } catch (err) {
      setInviteStatus("failed");
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  async function onPublicar(pubId: string, estado: string) {
    try {
      await setPublicacionEstado(pubId, estado, undefined, publicacionObs.trim() || undefined);
      setMsg(`Estado → ${labelEstadoPublicacion(estado)}`);
      setError(null);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  async function onPromover() {
    if (!entidadId) return;
    const ref = contratoRef.trim();
    if (!ref) {
      setError("Indique la referencia del contrato antes de promover a cliente.");
      return;
    }
    try {
      await promoverEntidadCliente(entidadId, ref);
      setMsg("Promovido a cliente");
      setError(null);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  const entidad = detail?.entidad as Record<string, unknown> | undefined;
  const publicaciones = (detail?.publicaciones as Record<string, unknown>[]) ?? [];

  return (
    <section className="panel compact-panel">
      <div className="external-space-head">
        <div>
          <h2>Espacio externo</h2>
          <p className="muted small">Controle qué información puede ver la empresa y gestione su acceso externo.</p>
        </div>
        {entidad && <span className="external-relation-badge">{labelEstadoRelacion(String(entidad.estado_relacion))}</span>}
      </div>
      {msg && <p className="success-banner">{msg}</p>}
      {error && <p className="error-banner">{error}</p>}

      {!entidadId && (
        <button type="button" className="btn primary" onClick={onCrearEntidad}>
          Vincular entidad externa al expediente
        </button>
      )}

      {entidad && (
        <>
          <h3 className="external-section-title">Publicaciones</h3>
          <label className="muted small">
            Observación de publicación (opcional)
            <input
              type="text"
              value={publicacionObs}
              onChange={(ev) => setPublicacionObs(ev.target.value)}
              placeholder="Motivo o nota de la publicación"
            />
          </label>
          <div className="external-publications-grid" role="table" aria-label="Publicaciones externas">
            <div className="external-publications-grid__head" role="row">
              <span>Paquete</span><span>Estado</span><span>Versión</span><span>Acciones</span>
            </div>
            {publicaciones.map((p) => (
              <div className="external-publications-grid__row" role="row" key={String(p.id)}>
                <strong>{String(p.paquete)}</strong>
                <span>{labelEstadoPublicacion(String(p.estado))}</span>
                <span>v{String(p.version)}</span>
                <span className="external-publications-grid__actions">
                  {String(p.estado) !== "PUBLICADO_EMPRESA" ? (
                    <>
                      <button type="button" className="btn small" onClick={() => onPublicar(String(p.id), "PREPARADO_PRESENTAR")}>Preparar</button>
                      <button type="button" className="btn small primary" onClick={() => onPublicar(String(p.id), "PUBLICADO_EMPRESA")}>Publicar</button>
                    </>
                  ) : <span className="muted">Publicado</span>}
                </span>
              </div>
            ))}
          </div>

          <h3 className="external-section-title">Invitar acceso externo</h3>
          <form onSubmit={onInvite} className="inline-form" autoComplete="off">
            <input name="email" type="email" autoComplete="off" placeholder="Correo del contacto" required />
            <input name="full_name" autoComplete="off" placeholder="Nombre del contacto" required />
                  <button type="submit" className={`btn ${inviteStatus === "sent" ? "success" : inviteStatus === "failed" ? "danger" : ""}`} disabled={inviteStatus === "sending"}>{inviteStatus === "sending" ? "Enviando..." : inviteStatus === "sent" ? "Enviado ✓" : inviteStatus === "failed" ? "Reintentar" : "Invitar"}</button>
          </form>

          {String(entidad.estado_relacion) !== "CLIENTE_CONTRATADO" && (
            <div className="inline-form">
              <label className="muted small">
                Referencia de contrato (obligatoria para promover)
                <input
                  type="text"
                  value={contratoRef}
                  onChange={(ev) => setContratoRef(ev.target.value)}
                  placeholder="Número o código del contrato firmado"
                  required
                />
              </label>
              <button type="button" className="btn" onClick={onPromover} disabled={!contratoRef.trim()}>
                Promover a cliente contratado
              </button>
            </div>
          )}
        </>
      )}
    </section>
  );
}
