import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import type { SupportCaseDetail } from "../api";
import {
  addSupportComment,
  assignSupportCase,
  closeSupportCase,
  fetchSupportCase,
  resolveSupportCase,
  updateSupportCaseStatus,
} from "../api";
import { usePermissions } from "../hooks/usePermissions";

export function SoporteCasoDetailPage() {
  const { caseId } = useParams<{ caseId: string }>();
  const { has } = usePermissions();
  const [data, setData] = useState<SupportCaseDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [comment, setComment] = useState("");
  const [resolucion, setResolucion] = useState("");
  const [responsableId, setResponsableId] = useState("");

  const load = useCallback(() => {
    if (!caseId) return;
    fetchSupportCase(caseId)
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar"));
  }, [caseId]);

  useEffect(() => {
    load();
  }, [load]);

  if (!caseId) return null;
  if (error) return <p className="error">{error}</p>;
  if (!data) return <p className="muted">Cargando caso…</p>;

  return (
    <div className="ops-page">
      <p><Link to="/soporte">← Volver a Mesa de Ayuda</Link></p>
      <header className="page-header">
        <h1>{data.referencia} — {data.asunto}</h1>
        <p className="muted">{data.tipo} · {data.estado} · Prioridad {data.prioridad} · SLA {data.sla_estado}</p>
      </header>

      <section className="panel">
        <h2>Resumen</h2>
        <p>{data.descripcion}</p>
        {data.correlation_id && <p className="muted">Correlation ID: {data.correlation_id}</p>}
        {data.modulo_relacionado && <p className="muted">Módulo: {data.modulo_relacionado} · {data.entidad_relacionada ?? ""}</p>}
        {data.resolucion && <p><strong>Resolución:</strong> {data.resolucion}</p>}
      </section>

      {has("support.assign") && (
        <section className="panel">
          <h2>Asignación</h2>
          <input placeholder="ID responsable" value={responsableId} onChange={(e) => setResponsableId(e.target.value)} />
          <button type="button" onClick={() => assignSupportCase(caseId, { responsable_id: responsableId || null }).then(load)}>
            Asignar
          </button>
          {has("support.update") && (
            <button type="button" onClick={() => updateSupportCaseStatus(caseId, { estado: "EN_PROCESO" }).then(load)}>
              Marcar en proceso
            </button>
          )}
        </section>
      )}

      {has("support.resolve") && (
        <section className="panel">
          <h2>Resolver</h2>
          <textarea rows={3} value={resolucion} onChange={(e) => setResolucion(e.target.value)} placeholder="Descripción de la resolución" />
          <button type="button" className="btn primary" onClick={() => resolveSupportCase(caseId, { resolucion, cerrar: false }).then(load)}>
            Resolver
          </button>
        </section>
      )}

      {has("support.close") && data.estado === "RESUELTO" && (
        <section className="panel">
          <button type="button" onClick={() => closeSupportCase(caseId, {}).then(load)}>Cerrar caso</button>
        </section>
      )}

      <section className="panel">
        <h2>Comentarios</h2>
        <ul>
          {data.comentarios.map((c) => (
            <li key={c.id}>
              <small>{new Date(c.created_at ?? "").toLocaleString()}</small>
              {c.es_interno && <em> (interno)</em>}: {c.cuerpo}
            </li>
          ))}
        </ul>
        <textarea rows={2} value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Agregar comentario" />
        <button type="button" onClick={() => addSupportComment(caseId, { cuerpo: comment }).then(() => { setComment(""); load(); })}>
          Comentar
        </button>
      </section>

      <section className="panel">
        <h2>Historial</h2>
        <table className="data-table compact-table">
          <thead><tr><th>Fecha</th><th>Acción</th><th>Detalle</th></tr></thead>
          <tbody>
            {data.historial.map((h) => (
              <tr key={h.id}>
                <td>{h.created_at ? new Date(h.created_at).toLocaleString() : "—"}</td>
                <td>{h.accion}</td>
                <td>{h.detalle ? JSON.stringify(h.detalle) : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
