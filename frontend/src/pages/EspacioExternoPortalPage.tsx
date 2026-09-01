import { FormEvent, useCallback, useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import {
  crearCasoSoporteExterno,
  entregarInformacionExterna,
  fetchMiEspacioEmpleadosIa,
  fetchMiEspacioEstado,
  fetchMiEspacioImplementacion,
  fetchMiEspacioInformes,
  fetchMiEspacioInicio,
  fetchMiEspacioInformacion,
  fetchMiEspacioSoporte,
  fetchMiEspacioVistaEntidad,
  subirAdjuntosExternos,
  descargarAdjuntoExterno,
  type MiEspacioContext,
} from "../api";
import { VistaEntidadPreview } from "../components/evaluacion/VistaEntidadPreview";
import { usePermissions } from "../hooks/usePermissions";
import { labelEstadoPublicacion, labelEstadoRelacion } from "../lib/evaluacionLabels";

type Tab =
  | "inicio"
  | "informacion"
  | "entregas"
  | "estado"
  | "resultados"
  | "propuesta"
  | "implementacion"
  | "empleados_ia"
  | "informes"
  | "soporte";

export function EspacioExternoPortalPage() {
  const { has } = usePermissions();
  const [ctx, setCtx] = useState<MiEspacioContext | null>(null);
  const [tab, setTab] = useState<Tab>("inicio");
  const [inicio, setInicio] = useState<Record<string, unknown> | null>(null);
  const [informacion, setInformacion] = useState<Record<string, unknown> | null>(null);
  const [estado, setEstado] = useState<Record<string, unknown> | null>(null);
  const [vista, setVista] = useState<Record<string, unknown> | null>(null);
  const [implementacion, setImplementacion] = useState<Record<string, unknown> | null>(null);
  const [empleadosIa, setEmpleadosIa] = useState<Record<string, unknown> | null>(null);
  const [informes, setInformes] = useState<Record<string, unknown> | null>(null);
  const [soporte, setSoporte] = useState<Record<string, unknown> | null>(null);
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
    if (tab === "implementacion") {
      fetchMiEspacioImplementacion().then(setImplementacion).catch((e) => setError(String(e)));
    }
    if (tab === "empleados_ia") {
      fetchMiEspacioEmpleadosIa().then(setEmpleadosIa).catch((e) => setError(String(e)));
    }
    if (tab === "informes") {
      fetchMiEspacioInformes().then(setInformes).catch((e) => setError(String(e)));
    }
    if (tab === "soporte") {
      fetchMiEspacioSoporte().then(setSoporte).catch((e) => setError(String(e)));
    }
  }, [tab]);

  if (!has("espacio_externo.portal")) {
    return <Navigate to="/" replace />;
  }

  const relacion = ctx?.estado_relacion ?? "";
  const esCliente = relacion === "CLIENTE_CONTRATADO";
  const seccionAccesible = (paquete: string) =>
    (ctx?.secciones ?? []).some((s) => s.paquete === paquete && s.accesible);

  const tabs: { id: Tab; label: string; show: boolean }[] = [
    { id: "inicio", label: "Inicio", show: true },
    { id: "informacion", label: "Información requerida", show: true },
    { id: "entregas", label: "Mis entregas", show: true },
    { id: "estado", label: "Estado", show: true },
    { id: "resultados", label: "Resumen ejecutivo", show: relacion !== "PROSPECTO_EVALUACION" },
    { id: "propuesta", label: "Propuesta", show: relacion === "PROSPECTO_RESULTADOS" || esCliente },
    { id: "implementacion", label: "Implementación", show: esCliente && seccionAccesible("IMPLEMENTACION") },
    { id: "empleados_ia", label: "Empleados IA", show: esCliente && seccionAccesible("EMPLEADOS_IA") },
    { id: "informes", label: "Informes", show: esCliente && seccionAccesible("INFORMES") },
    { id: "soporte", label: "Soporte", show: esCliente && seccionAccesible("SOPORTE") },
  ];

  async function onEntregar(e: FormEvent<HTMLFormElement>, itemId: string) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const contenido = String(fd.get("contenido") ?? "").trim();
    const fileInput = e.currentTarget.querySelector<HTMLInputElement>('input[type="file"]');
    const files = fileInput?.files ? Array.from(fileInput.files) : [];
    if (!contenido && files.length === 0) return;
    try {
      if (files.length > 0) {
        await subirAdjuntosExternos(itemId, files, contenido || undefined);
      } else {
        await entregarInformacionExterna({ item_id: itemId, contenido });
      }
      setMsg("Entrega registrada — en validación");
      fetchMiEspacioInformacion().then(setInformacion);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al entregar");
    }
  }

  async function onCrearCaso(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const asunto = String(fd.get("asunto") ?? "").trim();
    const descripcion = String(fd.get("descripcion") ?? "").trim();
    if (!asunto || !descripcion) return;
    try {
      await crearCasoSoporteExterno({ asunto, descripcion });
      setMsg("Caso de soporte creado");
      fetchMiEspacioSoporte().then(setSoporte);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al crear caso");
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
                      <textarea name="contenido" rows={3} placeholder="Su respuesta u observación…" />
                      <input type="file" name="adjuntos" multiple accept=".txt,.csv,.json,.pdf,.docx,.xlsx" />
                      <p className="muted small">Formatos: txt, csv, json, pdf, docx, xlsx (máx. 20 MB)</p>
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
                <li key={String(e.id)} className="entrega-card">
                  <strong>{String(e.titulo)}</strong> — {String(e.estado)} — v{String(e.version)}
                  {e.observacion_publica ? (
                    <p className="muted small">Complemento solicitado: {String(e.observacion_publica)}</p>
                  ) : null}
                  <ul className="adjuntos-list">
                    {((e.adjuntos as Record<string, unknown>[]) ?? []).map((a) => (
                      <li key={String(a.id)}>
                        {String(a.nombre)} — v{String(a.version)} — {String(a.estado)}
                        {" "}
                        <button
                          type="button"
                          className="btn link"
                          onClick={() => descargarAdjuntoExterno(String(a.id), String(a.nombre)).catch((err) => setError(String(err)))}
                        >
                          Descargar
                        </button>
                      </li>
                    ))}
                  </ul>
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

      {tab === "implementacion" && implementacion && (
        <section className="panel">
          <h2>Implementación</h2>
          <pre className="json-preview">{JSON.stringify(implementacion.implementacion, null, 2)}</pre>
        </section>
      )}

      {tab === "empleados_ia" && empleadosIa && (
        <section className="panel">
          <h2>Empleados IA</h2>
          <ul>
            {((empleadosIa.empleados as Record<string, unknown>[]) ?? []).map((e) => (
              <li key={String(e.id)}>
                <strong>{String(e.nombre)}</strong> — {String(e.estado)}
                <p className="muted small">{String(e.proposito ?? "")}</p>
              </li>
            ))}
          </ul>
        </section>
      )}

      {tab === "informes" && informes && (
        <section className="panel">
          <h2>Informes autorizados</h2>
          <ul>
            {((informes.informes as Record<string, unknown>[]) ?? []).map((i) => (
              <li key={String(i.id)}>
                {String(i.nombre)} — {String(i.estado)} — {String(i.fecha ?? "")}
              </li>
            ))}
          </ul>
        </section>
      )}

      {tab === "soporte" && soporte && (
        <section className="panel">
          <h2>Soporte</h2>
          <form onSubmit={onCrearCaso} className="entrega-form">
            <input name="asunto" placeholder="Asunto" required />
            <textarea name="descripcion" rows={3} placeholder="Descripción del caso" required />
            <button type="submit" className="btn primary">Crear caso</button>
          </form>
          <h3>Mis casos</h3>
          <ul>
            {((soporte.casos as Record<string, unknown>[]) ?? []).map((c) => (
              <li key={String(c.id)}>
                #{String(c.numero)} — {String(c.asunto)} — {String(c.estado)}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
