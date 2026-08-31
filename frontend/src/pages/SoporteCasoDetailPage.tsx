import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import type { SupportAssignee, SupportCaseDetail } from "../api";
import {
  addSupportComment,
  addSupportEvidence,
  assignSupportCase,
  closeSupportCase,
  escalateSupportCase,
  fetchSupportAssignees,
  fetchSupportCase,
  proposeSupportKnowledge,
  resolveSupportCase,
  updateSupportCaseDiagnosis,
  updateSupportCaseStatus,
  validateSupportResolution,
} from "../api";
import { ContextualHelp } from "../components/ContextualHelp";
import { usePermissions } from "../hooks/usePermissions";
import { ESTADO_ETIQUETAS, HELP_CASO_DETALLE, SLA_ETIQUETAS } from "../lib/soporteHelp";

type Tab = "resumen" | "actividad" | "diagnostico" | "evidencias" | "sla" | "trazabilidad";

function formatHistorialDetalle(detalle: Record<string, unknown> | null | undefined): string {
  if (!detalle) return "—";
  const parts: string[] = [];
  if (detalle.de && detalle.a) parts.push(`${String(detalle.de)} → ${String(detalle.a)}`);
  if (detalle.motivo) parts.push(`Motivo: ${String(detalle.motivo)}`);
  if (detalle.nota) parts.push(String(detalle.nota));
  if (detalle.resolucion) parts.push(String(detalle.resolucion));
  return parts.length ? parts.join(" · ") : JSON.stringify(detalle);
}

export function SoporteCasoDetailPage() {
  const { caseId } = useParams<{ caseId: string }>();
  const { has } = usePermissions();
  const [data, setData] = useState<SupportCaseDetail | null>(null);
  const [agents, setAgents] = useState<SupportAssignee[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("resumen");
  const [comment, setComment] = useState("");
  const [resolucion, setResolucion] = useState("");
  const [responsableId, setResponsableId] = useState("");
  const [diag, setDiag] = useState({ sintoma: "", hipotesis: "", causa_probable: "", causa_validada: "" });
  const [evidencia, setEvidencia] = useState({ tipo: "LOG", referencia: "", descripcion: "" });
  const [kbTitulo, setKbTitulo] = useState("");
  const [kbContenido, setKbContenido] = useState("");

  const load = useCallback(() => {
    if (!caseId) return;
    fetchSupportCase(caseId)
      .then((d) => {
        setData(d);
        setResponsableId(d.responsable_id ?? "");
        setDiag({
          sintoma: d.sintoma ?? "",
          hipotesis: d.hipotesis ?? "",
          causa_probable: d.causa_probable ?? "",
          causa_validada: d.causa_validada ?? "",
        });
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar"));
  }, [caseId]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (!has("support.assign")) return;
    fetchSupportAssignees()
      .then(setAgents)
      .catch(() => setAgents([]));
  }, [has]);

  if (!caseId) return null;
  if (error) return <p className="error">{error}</p>;
  if (!data) return <p className="muted">Cargando caso…</p>;

  const tabs: { id: Tab; label: string }[] = [
    { id: "resumen", label: "Resumen" },
    { id: "actividad", label: "Actividad" },
    { id: "diagnostico", label: "Diagnóstico" },
    { id: "evidencias", label: "Evidencias" },
    { id: "sla", label: "SLA" },
    { id: "trazabilidad", label: "Trazabilidad" },
  ];

  return (
    <div className="ops-page">
      <p><Link to="/soporte">← Volver a Mesa de Ayuda</Link></p>
      <header className="page-header">
        <div className="page-header-row">
          <div>
            <h1>{data.referencia} — {data.asunto}</h1>
            <p className="muted">
              {data.tipo} · {ESTADO_ETIQUETAS[data.estado] ?? data.estado} · Prioridad {data.prioridad}
              {data.es_incidente_mayor ? " · Incidente mayor" : ""}
            </p>
          </div>
          <ContextualHelp content={HELP_CASO_DETALLE} />
        </div>
      </header>

      <nav className="tab-bar" aria-label="Secciones del caso">
        {tabs.map((t) => (
          <button key={t.id} type="button" className={tab === t.id ? "tab active" : "tab"} onClick={() => setTab(t.id)}>
            {t.label}
          </button>
        ))}
      </nav>

      {tab === "resumen" && (
        <>
          <section className="panel">
            <h2>Resumen</h2>
            <p>{data.descripcion}</p>
            {data.correlation_id && <p className="muted">Correlación: {data.correlation_id}</p>}
            {data.servicio_componente && <p className="muted">Servicio: {data.servicio_componente}</p>}
            {data.responsable_nombre && (
              <p><strong>Responsable:</strong> {data.responsable_nombre}{data.responsable_email ? ` (${data.responsable_email})` : ""}</p>
            )}
            {data.resolucion && <p><strong>Resolución:</strong> {data.resolucion}</p>}
            {data.validacion_solicitante && (
              <p><strong>Validación solicitante:</strong> {data.validacion_solicitante}</p>
            )}
          </section>

          {has("support.assign") && (
            <section className="panel">
              <h2>Asignación</h2>
              <select id="responsable-select" value={responsableId} onChange={(e) => setResponsableId(e.target.value)}>
                <option value="">— Sin asignar —</option>
                {agents.map((a) => (
                  <option key={a.id} value={a.id}>{a.nombre} ({a.username})</option>
                ))}
              </select>
              <button type="button" onClick={() => assignSupportCase(caseId, { responsable_id: responsableId || null }).then(load)}>
                Asignar
              </button>
              {has("support.update") && (
                <>
                  <button type="button" onClick={() => updateSupportCaseStatus(caseId, { estado: "EN_ANALISIS" }).then(load)}>
                    Marcar en análisis
                  </button>
                  <button
                    type="button"
                    onClick={() => escalateSupportCase(caseId, { motivo: "CRITICIDAD", nota: "Escalamiento manual" }).then(load)}
                  >
                    Escalar
                  </button>
                </>
              )}
            </section>
          )}

          {has("support.resolve") && data.estado !== "CERRADO" && (
            <section className="panel">
              <h2>Resolver</h2>
              <textarea rows={3} value={resolucion} onChange={(e) => setResolucion(e.target.value)} placeholder="Descripción de la resolución" />
              <button type="button" className="btn primary" onClick={() => resolveSupportCase(caseId, { resolucion, cerrar: false }).then(load)}>
                Resolver (pendiente validación)
              </button>
            </section>
          )}

          {data.estado === "RESUELTO" && data.solicitante_id && (
            <section className="panel">
              <h2>Validación</h2>
              <button type="button" className="btn primary" onClick={() => validateSupportResolution(caseId, { aceptada: true }).then(load)}>
                Aceptar resolución
              </button>
              <button type="button" onClick={() => validateSupportResolution(caseId, { aceptada: false, comentario: "Requiere más trabajo" }).then(load)}>
                Rechazar
              </button>
            </section>
          )}

          {has("support.close") && data.estado === "RESUELTO" && (
            <section className="panel">
              <button type="button" onClick={() => closeSupportCase(caseId, {}).then(load)}>Cerrar caso</button>
            </section>
          )}
        </>
      )}

      {tab === "actividad" && (
        <section className="panel">
          <h2>Comunicaciones y comentarios</h2>
          <ul>
            {data.comentarios.map((c) => (
              <li key={c.id}>
                <small>{c.created_at ? new Date(c.created_at).toLocaleString() : ""}</small>
                {c.es_interno && <em> (interno)</em>}: {c.cuerpo}
              </li>
            ))}
          </ul>
          <textarea rows={2} value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Agregar comentario" />
          <button type="button" onClick={() => addSupportComment(caseId, { cuerpo: comment }).then(() => { setComment(""); load(); })}>
            Comentar
          </button>
        </section>
      )}

      {tab === "diagnostico" && (
        <section className="panel">
          <h2>Diagnóstico</h2>
          <p className="muted">Registre síntoma, hipótesis y causa validada por separado.</p>
          {(["sintoma", "hipotesis", "causa_probable", "causa_validada"] as const).map((field) => (
            <label key={field}>
              {field.replace(/_/g, " ")}
              <textarea
                rows={2}
                value={diag[field]}
                onChange={(e) => setDiag({ ...diag, [field]: e.target.value })}
                disabled={!has("support.update")}
              />
            </label>
          ))}
          {has("support.update") && (
            <button type="button" onClick={() => updateSupportCaseDiagnosis(caseId, diag).then(load)}>
              Guardar diagnóstico
            </button>
          )}
          {has("support.resolve") && (
            <div className="panel-sub">
              <h3>Proponer artículo de conocimiento</h3>
              <input value={kbTitulo} onChange={(e) => setKbTitulo(e.target.value)} placeholder="Título" />
              <textarea rows={3} value={kbContenido} onChange={(e) => setKbContenido(e.target.value)} placeholder="Contenido propuesto (requiere revisión)" />
              <button
                type="button"
                onClick={() => proposeSupportKnowledge({ titulo: kbTitulo, contenido: kbContenido, case_id: caseId }).then(() => setKbTitulo(""))}
              >
                Proponer (no publica automáticamente)
              </button>
            </div>
          )}
        </section>
      )}

      {tab === "evidencias" && (
        <section className="panel">
          <h2>Evidencias</h2>
          <ul>
            {(data.evidencias ?? []).map((e) => (
              <li key={e.id}><strong>{e.tipo}</strong>: {e.referencia} {e.descripcion ? `— ${e.descripcion}` : ""}</li>
            ))}
          </ul>
          <label>
            Tipo
            <select value={evidencia.tipo} onChange={(ev) => setEvidencia({ ...evidencia, tipo: ev.target.value })}>
              <option value="LOG">Log</option>
              <option value="CAPTURA">Captura</option>
              <option value="DOCUMENTO">Documento</option>
              <option value="ERROR">Error</option>
              <option value="EVENTO">Evento</option>
              <option value="EJECUCION">Ejecución</option>
              <option value="OBJETO_EIAAX">Objeto EIAAX</option>
            </select>
          </label>
          <input value={evidencia.referencia} onChange={(e) => setEvidencia({ ...evidencia, referencia: e.target.value })} placeholder="Referencia (URI, ID, ruta)" />
          <button
            type="button"
            onClick={() => addSupportEvidence(caseId, evidencia).then(() => { setEvidencia({ tipo: "LOG", referencia: "", descripcion: "" }); load(); })}
          >
            Agregar evidencia
          </button>
        </section>
      )}

      {tab === "sla" && (
        <section className="panel">
          <h2>SLA</h2>
          <p>Estado: <strong>{SLA_ETIQUETAS[data.sla_estado ?? ""] ?? data.sla_estado ?? "Sin SLA"}</strong></p>
          {data.primera_respuesta_limite && (
            <p>Primera respuesta antes de: {new Date(data.primera_respuesta_limite).toLocaleString()}</p>
          )}
          {data.resolucion_limite && (
            <p>Resolución objetivo: {new Date(data.resolucion_limite).toLocaleString()}</p>
          )}
          {!data.resolucion_limite && !data.primera_respuesta_limite && (
            <p className="muted">No hay compromiso SLA configurado para este caso.</p>
          )}
        </section>
      )}

      {tab === "trazabilidad" && (
        <section className="panel">
          <h2>Historial y trazabilidad</h2>
          <table className="data-table compact-table">
            <thead><tr><th>Fecha</th><th>Acción</th><th>Detalle</th></tr></thead>
            <tbody>
              {data.historial.map((h) => (
                <tr key={h.id}>
                  <td>{h.created_at ? new Date(h.created_at).toLocaleString() : "—"}</td>
                  <td>{h.accion}</td>
                  <td>{formatHistorialDetalle(h.detalle)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {data.problema && (
            <p className="muted">Problema vinculado: {String((data.problema as Record<string, string>).referencia)}</p>
          )}
        </section>
      )}
    </div>
  );
}
