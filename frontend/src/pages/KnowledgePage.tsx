import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import type { KnowledgeDocumentItem } from "../api";
import {
  deactivateKnowledgeDocument,
  deleteKnowledgeDocument,
  downloadKnowledgeDocument,
  fetchKnowledgeDocuments,
  reprocessKnowledgeDocument,
  uploadKnowledgeFile,
} from "../api";

const STATUS_LABELS: Record<string, string> = {
  PENDING: "Pendiente",
  PROCESSING: "Procesando",
  AVAILABLE: "Disponible",
  ERROR: "Con error",
  INACTIVE: "Inactivo",
};

const SOURCE_LABELS: Record<string, string> = {
  FILE: "Archivo",
  TEXT: "Texto",
  URL: "URL",
  INTEGRATION: "Integración",
};

function formatBytes(size: number | null | undefined) {
  if (!size) return "—";
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

export function KnowledgePage() {
  const [rows, setRows] = useState<KnowledgeDocumentItem[]>([]);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [sourceType, setSourceType] = useState("");
  const [sortAsc, setSortAsc] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [showCols, setShowCols] = useState({
    tipo: true,
    fuente: true,
    empresa: false,
    tamano: true,
    carga: true,
    actualizacion: true,
    procesado: true,
    uso: true,
  });

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await fetchKnowledgeDocuments();
      setRows(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const filtered = useMemo(
    () =>
      rows
        .filter((row) => {
          const haystack = `${row.name} ${row.file_type || ""}`.toLowerCase();
          return (
            (!search || haystack.includes(search.toLowerCase())) &&
            (!status || row.status === status) &&
            (!sourceType || row.source_type === sourceType)
          );
        })
        .sort((a, b) => (sortAsc ? 1 : -1) * a.updated_at.localeCompare(b.updated_at)),
    [rows, search, status, sourceType, sortAsc],
  );

  const onUpload = async (file: File | null) => {
    if (!file) return;
    setUploading(true);
    setError("");
    try {
      await uploadKnowledgeFile(file);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setUploading(false);
    }
  };

  const onDelete = async (id: string) => {
    if (!window.confirm("¿Eliminar este documento?")) return;
    await deleteKnowledgeDocument(id);
    await load();
  };

  const onReprocess = async (id: string) => {
    await reprocessKnowledgeDocument(id);
    await load();
  };

  const onDeactivate = async (id: string) => {
    await deactivateKnowledgeDocument(id);
    await load();
  };

  const onDownload = async (row: KnowledgeDocumentItem) => {
    setError("");
    try {
      await downloadKnowledgeDocument(row.id, row.original_filename || row.name);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Centro de conocimiento</h1>
        <p className="muted">Fuentes y documentos empresariales para Empleados IA autorizados.</p>
      </header>

      <div className="ops-actions">
        <label className="btn primary" title="Cargar archivo">
          {uploading ? "Cargando…" : "+ Cargar archivo"}
          <input
            type="file"
            hidden
            accept=".txt,.csv,.json,.pdf,.docx,.xlsx"
            onChange={(e) => void onUpload(e.target.files?.[0] || null)}
          />
        </label>
        <input
          placeholder="Buscar por nombre o tipo"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="Buscar"
        />
        <select value={status} onChange={(e) => setStatus(e.target.value)} aria-label="Filtrar estado">
          <option value="">Todos los estados</option>
          {Object.entries(STATUS_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        <select value={sourceType} onChange={(e) => setSourceType(e.target.value)} aria-label="Filtrar fuente">
          <option value="">Todas las fuentes</option>
          {Object.entries(SOURCE_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        <button type="button" className="btn" title="Ordenar por actualización" onClick={() => setSortAsc(!sortAsc)}>
          ↕ Actualización
        </button>
        <button type="button" className="btn" title="Actualizar lista" onClick={() => void load()}>
          ↻
        </button>
      </div>

      <div className="panel" style={{ marginBottom: 12 }}>
        <span className="muted">Columnas: </span>
        {Object.entries({
          tipo: "Tipo",
          fuente: "Fuente",
          empresa: "Empresa",
          tamano: "Tamaño",
          carga: "Fecha de carga",
          actualizacion: "Fecha de actualización",
          procesado: "Procesado",
          uso: "Uso",
        }).map(([key, label]) => (
          <label key={key} style={{ marginRight: 10 }}>
            <input
              type="checkbox"
              checked={showCols[key as keyof typeof showCols]}
              onChange={(e) => setShowCols((prev) => ({ ...prev, [key]: e.target.checked }))}
            />{" "}
            {label}
          </label>
        ))}
      </div>

      {loading && <p className="muted">Cargando documentos…</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && filtered.length === 0 && (
        <p className="muted">No hay documentos para los filtros seleccionados.</p>
      )}

      <div className="panel table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Nombre</th>
              {showCols.tipo && <th>Tipo</th>}
              {showCols.fuente && <th>Fuente</th>}
              <th>Estado</th>
              {showCols.empresa && <th>Empresa</th>}
              {showCols.tamano && <th>Tamaño</th>}
              {showCols.carga && <th>Fecha de carga</th>}
              {showCols.actualizacion && <th>Fecha de actualización</th>}
              {showCols.procesado && <th>Procesado</th>}
              {showCols.uso && <th>Uso</th>}
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((row) => (
              <tr key={row.id}>
                <td>
                  <strong>{row.name}</strong>
                  {row.error_message && <div className="error">{row.error_message}</div>}
                </td>
                {showCols.tipo && <td>{row.file_type || "—"}</td>}
                {showCols.fuente && <td>{SOURCE_LABELS[row.source_type] || row.source_type}</td>}
                <td>
                  <span className={`badge status-${row.status}`}>{STATUS_LABELS[row.status] || row.status}</span>
                </td>
                {showCols.empresa && <td className="mono">{row.organization_id.slice(0, 8)}…</td>}
                {showCols.tamano && <td>{formatBytes(row.size_bytes)}</td>}
                {showCols.carga && <td>{new Date(row.created_at).toLocaleString()}</td>}
                {showCols.actualizacion && <td>{new Date(row.updated_at).toLocaleString()}</td>}
                {showCols.procesado && <td>{row.processed_at ? new Date(row.processed_at).toLocaleString() : "—"}</td>}
                {showCols.uso && <td>{row.association_count || 0}</td>}
                <td className="notification-actions">
                  <Link to={`/conocimiento/${row.id}`} title="Ver detalle">
                    👁
                  </Link>
                  <button type="button" title="Reprocesar" onClick={() => void onReprocess(row.id)}>
                    ↻
                  </button>
                  <button type="button" title="Descargar" onClick={() => void onDownload(row)}>
                    ⬇
                  </button>
                  <button type="button" title="Desactivar" onClick={() => void onDeactivate(row.id)}>
                    ⏸
                  </button>
                  <button type="button" title="Eliminar" onClick={() => void onDelete(row.id)}>
                    ×
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
