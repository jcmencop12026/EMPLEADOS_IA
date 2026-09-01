import { FormEvent, useCallback, useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import {
  entregarInformacionExterna,
  fetchMiEspacioEstado,
  fetchMiEspacioInicio,
  fetchMiEspacioInformacion,
  fetchMiEspacioVistaEntidad,
  type MiEspacioContext,
} from "../api";
import { VistaEntidadPreview } from "../components/evaluacion/VistaEntidadPreview";
import { usePermissions } from "../hooks/usePermissions";
import { labelEstadoPublicacion, labelEstadoRelacion } from "../lib/evaluacionLabels";

type Tab = "inicio" | "informacion" | "entregas" | "estado" | "resultados" | "propuesta";

export function EspacioExternoPortalPage() {
  const { has } = usePermissions();
  const [ctx, setCtx] = useState<MiEspacioContext | null>(null);
  const [tab, setTab] = useState<Tab>("inicio");
  const [inicio, setInicio] = useState<Record<string, unknown> | null>(null);
  const [informacion, setInformacion] = useState<Record<string, unknown> | null>(null);
  const [estado, setEstado] = useState<Record<string, unknown> | null>(null);
  const [vista, setVista] = useState<Record<string, unknown> | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadCtx = useCallback(() => {
    fetchMiEspacioInicio()
      .then((data) => {
        setInicio(data);
        setCtx({
          entidad: data.entidad as MiEspacioContext["entidad"],
          rol_externo: String(data.rol_externo ?? "PROSPECTO"),
          estado_relacion: String(data.estado_relacion ?? ""),
          secciones: (data.secciones as MiEspacioContext["secciones"]) ?? [],
        });
        setError(null);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Error"));
  }, []);

  useEffect(() => { loadCtx(); }, [loadCtx]);

  useEffect(() => {
    if (tab === "informacion" || tab === "entregas") {
      fetchMiEspacioInformacion().then(setInformacion).catch(() => undefined);
    }
    if (tab === "estado") {
      fetchMiEspacioEstado().then(setEstado).catch(() => undefined);
    }
    if (tab === "resultados") {
      fetchMiEspacioVistaEntidad("RESULTADOS").then(setVista).catch((e) => setError(String(e)));
    }
    if (tab === "propuesta") {
      fetchMiEspacioVistaEntidad("PROPUESTA").then(setVista).catch((e) => setError(String(e)));
    }
  }, [tab]);

  if (!has("espacio_externo.portal")) {
    return <Navigate to="/" replace />;
  }

  const relacion = ctx?.estado_relacion ?? "";
  const tabs: { id: Tab; label: string; show: boolean }[] = [
    { id: "inicio", label: "Inicio", show: true },
    { id: "informacion", label: "Información requerida", show: relacion === "PROSPECTO_EVALUACION" || relacion === "PROSPECTO_RESULTADOS" || relacion === "CLIENTE_CONTRATADO" },
    { id: "entregas", label: "Mis entregas", show: true },
    { id: "estado", label: "Estado", show: true },
    { id: "resultados", label: "Resumen ejecutivo", show: relacion !== "PROSPECTO_EVALUACION" },
    { id: "propuesta", label: "Propuesta", show: relacion === "PROSPECTO_RESULTADOS" || relacion === "CLIENTE_CONTRATADO" },
  ];

  async function onEntregar(e: FormEvent<HTMLFormElement>, itemId: string) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const contenido = String(fd.get("contenido") ?? "").trim();
    if (!contenido) return;
    try {
      await entregarInformacionExterna({ item_id: itemId, contenido });
      setMsg("Entrega registrada — en validación");
      fetchMiEspacioInformacion().then(setInformacion);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al entregar");
    }
  }

  return (
    <div className="page espacio-externo-portal">
      <header className="page-header">
        <h1>Mi espacio — {ctx?.entidad?.nombre ?? "Empresa"}</h1>
        <p className="muted">
          {labelEstadoRelacion(relacion)} · Rol: {ctx?.rol_externo ?? "—"}
        </p>
      </header>

      {msg && <p className="success-banner">{msg}</p>}
      {error && <p className="error-banner">{error}</p>}

      <nav className="tab-nav">
        {tabs.filter((t) => t.show).map((t) => (
          <button
            key={t.id}
            type="button"
            className={tab === t.id ? "tab active" : "tab"}
            onClick={() => { setTab(t.id); setMsg(null); setError(null); }}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {tab === "inicio" && inicio && (
        <section className="panel">
          <h2>Bienvenido</h2>
          <p>Expediente: <strong>{String((inicio.expediente as Record<string, unknown>)?.codigo ?? "—")}</strong></p>
          <p>{String((inicio.expediente as Record<string, unknown>)?.objetivo ?? "")}</p>
          <h3>Secciones disponibles</h3>
          <ul>
            {(ctx?.secciones ?? []).map((s) => (
              <li key={s.paquete}>
                {s.paquete} — {labelEstadoPublicacion(s.estado_publicacion)}
                {s.accesible ? " ✓" : " (pendiente publicación)"}
              </li>
            ))}
          </ul>
        </section>
      )}

      {(tab === "informacion" || tab === "entregas") && informacion && (
        <section className="panel">
          <h2>{tab === "informacion" ? "Información requerida" : "Mis entregas"}</h2>
          {tab === "informacion" && (
            <ul className="info-solicitudes">
              {((informacion.solicitudes as Record<string, unknown>[]) ?? []).map((s) => (
                <li key={String(s.id)} className="info-solicitud-card">
                  <strong>{String(s.etiqueta)}</strong>
                  <p className="muted small">{String(s.explicacion ?? "")}</p>
                  <span className="badge">{String(s.estado_validacion ?? s.estado)}</span>
                  {s.puede_entregar && (
                    <form onSubmit={(e) => onEntregar(e, String(s.id))} className="entrega-form">
                      <textarea name="contenido" rows={3} placeholder="Su respuesta o evidencia…" required />
                      <button type="submit" className="btn primary">Entregar</button>
                    </form>
                  )}
                </li>
              ))}
            </ul>
          )}
          {tab === "entregas" && (
            <ul>
              {((informacion.entregas as Record<string, unknown>[]) ?? []).map((e) => (
                <li key={String(e.id)}>
                  {String(e.titulo)} — {String(e.estado)} — v{String(e.version)}
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      {tab === "estado" && estado && (
        <section className="panel">
          <h2>Estado del proceso</h2>
          <p>Información completada: {String(estado.porcentaje_informacion)}%</p>
          <p>
            Información mínima suficiente:{" "}
            {estado.informacion_minima_suficiente ? "Sí" : "Pendiente"}
          </p>
          {(estado.pendientes as string[] | undefined)?.length ? (
            <>
              <h3>Pendientes</h3>
              <ul>{(estado.pendientes as string[]).map((p) => <li key={p}>{p}</li>)}</ul>
            </>
          ) : (
            <p className="muted">No hay requisitos pendientes.</p>
          )}
        </section>
      )}

      {(tab === "resultados" || tab === "propuesta") && vista && (
        <section className="panel vista-entidad-preview">
          <VistaEntidadPreview data={(vista.vista as Record<string, unknown>) ?? {}} />
        </section>
      )}
    </div>
  );
}
