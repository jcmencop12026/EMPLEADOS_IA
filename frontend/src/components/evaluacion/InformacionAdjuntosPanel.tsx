import { useCallback, useEffect, useRef, useState } from "react";
import {
  descargarAdjuntoInterno,
  fetchAdjuntosInformacion,
  subirAdjuntosOperador,
  type AdjuntoEntregaItem,
} from "../../api";

type Props = {
  expedienteId: string;
  itemId: string;
  editable: boolean;
};

export function InformacionAdjuntosPanel({ expedienteId, itemId, editable }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [adjuntos, setAdjuntos] = useState<AdjuntoEntregaItem[]>([]);
  const [entregaId, setEntregaId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchAdjuntosInformacion(expedienteId, itemId)
      .then((r) => {
        setAdjuntos(r.adjuntos);
        setEntregaId(r.entrega_id);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar adjuntos"))
      .finally(() => setLoading(false));
  }, [expedienteId, itemId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function onFilesSelected(files: FileList | null) {
    if (!files?.length || !editable) return;
    setUploading(true);
    setError(null);
    try {
      await subirAdjuntosOperador(expedienteId, itemId, Array.from(files));
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo subir el archivo");
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <div className="info-adjuntos-panel">
      <div className="info-adjuntos-head">
        <span className="muted small">Evidencias recibidas</span>
        {editable && (
          <>
            <input
              ref={inputRef}
              type="file"
              multiple
              className="info-adjuntos-input"
              accept=".pdf,.docx,.xlsx,.csv,.txt,.json"
              onChange={(e) => void onFilesSelected(e.target.files)}
            />
            <button
              type="button"
              className="btn small secondary"
              disabled={uploading}
              onClick={() => inputRef.current?.click()}
            >
              {uploading ? "Subiendo…" : "Cargar documento"}
            </button>
          </>
        )}
      </div>
      {loading && <p className="muted small">Cargando adjuntos…</p>}
      {error && <p className="error small">{error}</p>}
      {!loading && adjuntos.length === 0 && (
        <p className="muted small">
          {editable
            ? "Sin documentos. Cargue archivos recibidos de la IPS o empresa (PDF, Excel, CSV, etc.)."
            : "Sin documentos asociados."}
        </p>
      )}
      {adjuntos.length > 0 && (
        <ul className="info-adjuntos-list">
          {adjuntos.map((a) => (
            <li key={a.id}>
              <span className="info-adjunto-name" title={a.nombre}>
                {a.nombre}
              </span>
              <span className="muted small">{a.estado}</span>
              <button
                type="button"
                className="btn-link small"
                onClick={() => void descargarAdjuntoInterno(a.id, a.nombre)}
              >
                Descargar
              </button>
            </li>
          ))}
        </ul>
      )}
      {entregaId && <p className="muted small">Entrega: {entregaId.slice(0, 8)}…</p>}
    </div>
  );
}
