import { FormEvent, useCallback, useEffect, useState } from "react";
import {
  createEntidadExterna,
  fetchEntidadExterna,
  inviteAccesoExterno,
  promoverEntidadCliente,
  setPublicacionEstado,
} from "../../api";
import { labelEstadoPublicacion, labelEstadoRelacion } from "../../lib/evaluacionLabels";

type Props = { expedienteId: string };

export function EspacioExternoAdminPanel({ expedienteId }: Props) {
  const [entidadId, setEntidadId] = useState<string | null>(null);
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    if (!entidadId) return;
    fetchEntidadExterna(entidadId).then(setDetail).catch(() => undefined);
  }, [entidadId]);

  useEffect(() => { load(); }, [load]);

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
    try {
      await inviteAccesoExterno(entidadId, {
        email: String(fd.get("email")),
        full_name: String(fd.get("full_name")),
        password: String(fd.get("password") || "Prospecto2026!"),
      });
      setMsg("Acceso invitado");
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  async function onPublicar(pubId: string, estado: string) {
    try {
      await setPublicacionEstado(pubId, estado, "empresa@externa.test", "Publicación V1");
      setMsg(`Estado → ${labelEstadoPublicacion(estado)}`);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }

  async function onPromover() {
    if (!entidadId) return;
    try {
      await promoverEntidadCliente(entidadId, "CONTRATO-V1");
      setMsg("Promovido a cliente");
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
            <input name="password" type="password" placeholder="Contraseña inicial" />
            <button type="submit" className="btn">Invitar</button>
          </form>

          {String(entidad.estado_relacion) !== "CLIENTE_CONTRATADO" && (
            <p>
              <button type="button" className="btn" onClick={onPromover}>
                Promover a cliente contratado
              </button>
            </p>
          )}
        </>
      )}
    </section>
  );
}
