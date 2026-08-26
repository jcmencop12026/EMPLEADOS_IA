import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import type { KnowledgeActivityItem, KnowledgeDocumentDetail } from "../api";
import {
  fetchKnowledgeActivity,
  fetchKnowledgeDocument,
  reprocessKnowledgeDocument,
  updateKnowledgeDocument,
} from "../api";

const STATUS_LABELS: Record<string, string> = {
  PENDING: "Pendiente",
  PROCESSING: "Procesando",
  AVAILABLE: "Disponible",
  ERROR: "Con error",
  INACTIVE: "Inactivo",
};

type Tab = "resumen" | "contenido" | "metadatos" | "asociaciones" | "actividad";

export function KnowledgeDetailPage() {
  const { documentId } = useParams<{ documentId: string }>();
  const [detail, setDetail] = useState<KnowledgeDocumentDetail | null>(null);
  const [activity, setActivity] = useState<KnowledgeActivityItem[]>([]);
  const [tab, setTab] = useState<Tab>("resumen");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState("");
  const [saving, setSaving] = useState(false);

  const load = async () => {
    if (!documentId) return;
    setLoading(true);
    setError("");
    try {
      const [doc, act] = await Promise.all([
        fetchKnowledgeDocument(documentId),
        fetchKnowledgeActivity(documentId),
      ]);
      setDetail(doc);
      setName(doc.name);
      setActivity(act);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [documentId]);

  const saveName = async () => {
    if (!documentId) return;
    setSaving(true);
    try {
      const updated = await updateKnowledgeDocument(documentId, { name });
      setDetail(updated);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <p className="muted">Cargando documento…</p>;
  if (!detail && error) return <p className="error">{error}</p>;
  if (!detail) return <p className="muted">El documento no existe o no está disponible.</p>;

  return (
    <div className="ops-page">
      <header className="page-header">
        <Link to="/conocimiento" className="muted">
          ← Centro de conocimiento
        </Link>
        <h1>{detail.name}</h1>
        <p className="muted">
          Estado: {STATUS_LABELS[detail.status] || detail.status} · Versión {detail.version}
        </p>
      </header>

      {error && <p className="error">{error}</p>}

      <div className="tab-bar">
        {(
          [
            ["resumen", "Resumen"],
            ["contenido", "Contenido"],
            ["metadatos", "Metadatos"],
            ["asociaciones", "Asociaciones"],
            ["actividad", "Actividad"],
          ] as Array<[Tab, string]>
        ).map(([key, label]) => (
          <button
            key={key}
            type="button"
            className={tab === key ? "active" : ""}
            onClick={() => setTab(key)}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "resumen" && (
        <section className="panel">
          <p>
            <strong>Tipo:</strong> {detail.file_type || detail.source_type}
          </p>
          <p>
            <strong>Tamaño:</strong> {detail.size_bytes ? `${detail.size_bytes} bytes` : "—"}
          </p>
          <p>
            <strong>Fragmentos:</strong> {detail.chunks_count}
          </p>
          <p>
            <strong>Creado:</strong> {new Date(detail.created_at).toLocaleString()}
          </p>
          <p>
            <strong>Actualizado:</strong> {new Date(detail.updated_at).toLocaleString()}
          </p>
          <div className="ops-actions">
            <input value={name} onChange={(e) => setName(e.target.value)} aria-label="Nombre" />
            <button type="button" className="btn primary" disabled={saving} onClick={() => void saveName()}>
              Guardar nombre
            </button>
            <button type="button" className="btn" onClick={() => void reprocessKnowledgeDocument(detail.id).then(load)}>
              Reprocesar
            </button>
          </div>
        </section>
      )}

      {tab === "contenido" && (
        <section className="panel">
          {detail.processed_content ? (
            <pre className="mono" style={{ whiteSpace: "pre-wrap" }}>
              {detail.processed_content}
            </pre>
          ) : (
            <p className="muted">No hay contenido procesado disponible.</p>
          )}
        </section>
      )}

      {tab === "metadatos" && (
        <section className="panel">
          {Object.keys(detail.metadata || {}).length > 0 ? (
            <pre className="mono">{JSON.stringify(detail.metadata, null, 2)}</pre>
          ) : (
            <p className="muted">Sin metadatos adicionales.</p>
          )}
        </section>
      )}

      {tab === "asociaciones" && (
        <section className="panel">
          <p>
            <strong>Asociaciones con Empleados IA:</strong> {detail.association_count}
          </p>
          <p className="muted">
            Las asignaciones se gestionan mediante el contrato de integración sin modificar el módulo de empleados.
          </p>
        </section>
      )}

      {tab === "actividad" && (
        <section className="panel table-wrap">
          {activity.length === 0 ? (
            <p className="muted">Sin actividad registrada.</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Acción</th>
                  <th>Detalle</th>
                </tr>
              </thead>
              <tbody>
                {activity.map((item) => (
                  <tr key={item.id}>
                    <td>{new Date(item.created_at).toLocaleString()}</td>
                    <td>{item.action}</td>
                    <td>{item.detail || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}
    </div>
  );
}
