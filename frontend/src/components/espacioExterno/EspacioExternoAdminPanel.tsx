import { FormEvent, useCallback, useEffect, useState } from "react";
import {
  createEntidadExterna,
  fetchEntidadExterna,
  fetchMe,
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
  const [publisherEmail, setPublisherEmail] = useState<string>("");
  const [publicacionObs, setPublicacionObs] = useState("");
  const [contratoRef, setContratoRef] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMe()
      .then((me) => setPublisherEmail(me.email ?? me.username))
      .catch(() => undefined);
  }, []);

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
      setMsg("Entidad empresa creada");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    }
  }

  async function onInvite(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!entidadId) return;
    const fd = new FormData(e.currentTarget);
    const password = String(fd.get("password") ?? "").trim();
    if (!password) {
      setError("La contraseña inicial es obligatoria para invitar acceso externo.");
      return;
    }
    try {
      await inviteAccesoExterno(entidadId, {
        email: String(fd.get("email")),
        full_name: String(fd.get("full_name")),
        password,
      });
      setMsg("Acceso invitado");
      setError(null);
      load();
      e.currentTarget.reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  async function onPublicar(pubId: string, estado: string) {
    if (!publisherEmail.trim()) {
      setError("No se pudo determinar el usuario publicador autenticado.");
      return;
    }
    try {
      await setPublicacionEstado(
        pubId,
        estado,
        publisherEmail.trim(),
        publicacionObs.trim() || undefined,
      );
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
      <h2>Espacio externo — publicar y visibilidad</h2>
      <p className="muted small">
        Publicar para consulta posterior, ver como empresa y controlar qué información ve el cliente.
      </p>
      {msg && <p className="success-banner">{msg}</p>}
      {error && <p className="error-banner">{error}</p>}

      {!entidadId && (
        <button type="button" className="btn primary" onClick={onCrearEntidad}>
          Crear entidad empresa / prospecto
        </button>
      )}

      {entidad && (
        <>
          <p>
            <strong>{String(entidad.nombre)}</strong> — {labelEstadoRelacion(String(entidad.estado_relacion))}
          </p>

          <h3>Publicaciones</h3>
          <label className="muted small">
            Observación de publicación (opcional)
            <input
              type="text"
              value={publicacionObs}
              onChange={(ev) => setPublicacionObs(ev.target.value)}
              placeholder="Motivo o nota de la publicación"
            />
          </label>
          <ul>
            {publicaciones.map((p) => (
              <li key={String(p.id)}>
                {String(p.paquete)} — {labelEstadoPublicacion(String(p.estado))} (v{String(p.version)})
                {String(p.estado) !== "PUBLICADO_EMPRESA" && (
                  <>
                    {" "}
                    <button type="button" className="btn-link" onClick={() => onPublicar(String(p.id), "PREPARADO_PRESENTAR")}>
                      Preparar
                    </button>
                    {" · "}
                    <button type="button" className="btn-link" onClick={() => onPublicar(String(p.id), "PUBLICADO_EMPRESA")}>
                      Publicar
                    </button>
                  </>
                )}
              </li>
            ))}
          </ul>

          <h3>Invitar acceso externo</h3>
          <form onSubmit={onInvite} className="inline-form">
            <input name="email" type="email" placeholder="email@empresa.com" required />
            <input name="full_name" placeholder="Nombre contacto" required />
            <input name="password" type="password" placeholder="Contraseña inicial (obligatoria)" required minLength={8} />
            <button type="submit" className="btn">Invitar</button>
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
