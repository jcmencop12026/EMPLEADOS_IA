import { FormEvent, useState } from "react";
import { preguntarEiaax } from "../../api";

const ACCIONES = [
  { id: "informacion_faltante", label: "¿Qué información falta?" },
  { id: "profundizar_hallazgo", label: "Profundizar hallazgo" },
  { id: "buscar_causas", label: "Buscar causas" },
  { id: "cuantificar_impacto", label: "Cuantificar impacto" },
  { id: "identificar_oportunidades", label: "Identificar oportunidades" },
  { id: "siguiente_analisis", label: "Siguiente análisis" },
] as const;

type Props = {
  expedienteId: string;
  open: boolean;
  onClose: () => void;
};

export function EiaaxAskPanel({ expedienteId, open, onClose }: Props) {
  const [mensaje, setMensaje] = useState("");
  const [accion, setAccion] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [resultado, setResultado] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!mensaje.trim() && !accion) return;
    setLoading(true);
    setError(null);
    try {
      const res = await preguntarEiaax(expedienteId, mensaje.trim() || "Consulta sobre el expediente", accion || undefined);
      setResultado(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al consultar EIAAX");
    } finally {
      setLoading(false);
    }
  }

  return (
    <aside className="eiaax-ask-panel" aria-label="Preguntar a EIAAX">
      <header className="eiaax-ask-header">
        <strong>Preguntar a EIAAX</strong>
        <button type="button" className="btn-icon" onClick={onClose} title="Cerrar panel">×</button>
      </header>
      <p className="muted small">Asistente contextual del expediente. Sin proveedor IA configurado, se muestra estado controlado.</p>
      <div className="eiaax-ask-actions">
        {ACCIONES.map((a) => (
          <button
            key={a.id}
            type="button"
            className={`btn small ${accion === a.id ? "primary" : ""}`}
            onClick={() => { setAccion(a.id); setMensaje(a.label); }}
          >
            {a.label}
          </button>
        ))}
      </div>
      <form onSubmit={onSubmit}>
        <label>
          Consulta
          <textarea
            value={mensaje}
            onChange={(e) => setMensaje(e.target.value)}
            rows={3}
            placeholder="Escriba su pregunta sobre este expediente…"
            disabled={loading}
          />
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit" className="btn primary" disabled={loading}>
          {loading ? "Consultando…" : "Enviar"}
        </button>
      </form>
      {resultado && (
        <div className="eiaax-ask-result panel compact-panel">
          {resultado.estado === "sin_proveedor" ? (
            <>
              <p className="warning-text">{String(resultado.mensaje)}</p>
              {resultado.contexto_expediente && (
                <pre className="code-block small">{JSON.stringify(resultado.contexto_expediente, null, 2)}</pre>
              )}
            </>
          ) : (
            <pre className="code-block small">{JSON.stringify(resultado.respuesta ?? resultado, null, 2)}</pre>
          )}
        </div>
      )}
    </aside>
  );
}
