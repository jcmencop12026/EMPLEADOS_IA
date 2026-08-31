import { useEffect, useState } from "react";
import {
  aprobarAccionExterna,
  crearAccionExterna,
  fetchAccionesExternas,
  fetchCapacidades,
  fetchPiiaxStatus,
  solicitarAccionExterna,
  type AccionExterna,
  type CapacidadExterna,
} from "../../api";
import { label, ESTADO_ACCION, TIPO_ACCION } from "../../lib/evaluacionLabels";
import { usePermissions } from "../../hooks/usePermissions";

type Props = {
  expedienteId: string;
  hallazgoId?: string;
  hallazgoTitulo?: string;
  onUpdated?: () => void;
};

export function AccionesExternasPanel({ expedienteId, hallazgoId, hallazgoTitulo, onUpdated }: Props) {
  const { has } = usePermissions();
  const [acciones, setAcciones] = useState<AccionExterna[]>([]);
  const [capacidades, setCapacidades] = useState<CapacidadExterna[]>([]);
  const [piiax, setPiiax] = useState<Record<string, unknown> | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ capacidad: "consultar_datos", tipo_accion: "LECTURA", titulo: "" });
  const [error, setError] = useState<string | null>(null);

  function load() {
    Promise.all([
      fetchAccionesExternas(expedienteId),
      fetchCapacidades(),
      fetchPiiaxStatus(),
    ]).then(([a, c, p]) => {
      setAcciones(a.items);
      setCapacidades(c.capacidades);
      setPiiax(p);
    }).catch(() => undefined);
  }

  useEffect(() => { load(); }, [expedienteId]);

  async function onCreate() {
    setError(null);
    try {
      await crearAccionExterna(expedienteId, {
        ...form,
        titulo: form.titulo || `Analizar fuentes — ${hallazgoTitulo ?? "expediente"}`,
        hallazgo_id: hallazgoId,
        solicitar: true,
      });
      setShowForm(false);
      load();
      onUpdated?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al crear acción");
    }
  }

  async function onAprobar(id: string, aprobado: boolean) {
    await aprobarAccionExterna(expedienteId, id, aprobado);
    load();
    onUpdated?.();
  }

  async function onSolicitar(id: string) {
    await solicitarAccionExterna(expedienteId, id);
    load();
    onUpdated?.();
  }

  const filtradas = hallazgoId ? acciones.filter((a) => a.hallazgo_id === hallazgoId) : acciones;

  return (
    <div className="acciones-externas-panel">
      <div className="piiax-status-bar">
        <span className={`piiax-dot ${piiax?.disponible ? "on" : "off"}`} />
        <span>{piiax?.disponible ? "PIIAX disponible" : "PIIAX no conectado"}</span>
        <span className="muted small">{String(piiax?.mensaje ?? "")}</span>
      </div>

      {has("evaluacion.accion.request") && (
        <button type="button" className="btn small" onClick={() => setShowForm((v) => !v)}>
          {showForm ? "Cancelar" : "Solicitar capacidad externa"}
        </button>
      )}

      {showForm && (
        <div className="panel compact-panel">
          <label>Capacidad
            <select value={form.capacidad} onChange={(e) => setForm({ ...form, capacidad: e.target.value })}>
              {capacidades.map((c) => (
                <option key={c.codigo} value={c.codigo}>{c.etiqueta}</option>
              ))}
            </select>
          </label>
          <label>Tipo
            <select value={form.tipo_accion} onChange={(e) => setForm({ ...form, tipo_accion: e.target.value })}>
              {Object.keys(TIPO_ACCION).map((k) => (
                <option key={k} value={k}>{TIPO_ACCION[k]}</option>
              ))}
            </select>
          </label>
          <label>Título<input value={form.titulo} onChange={(e) => setForm({ ...form, titulo: e.target.value })} placeholder="Ej. Analizar fuentes de datos" /></label>
          {error && <p className="error">{error}</p>}
          <button type="button" className="btn primary small" onClick={onCreate}>Crear y solicitar</button>
        </div>
      )}

      {filtradas.length === 0 && <p className="muted small">Sin acciones externas registradas.</p>}
      {filtradas.map((a) => (
        <article key={a.id} className="accion-externa-card">
          <header>
            <strong>{a.titulo}</strong>
            <span className="badge">{label(ESTADO_ACCION, a.estado)}</span>
          </header>
          <p className="muted small">{a.capacidad_etiqueta ?? a.capacidad} · {a.tipo_accion_etiqueta ?? a.tipo_accion}</p>
          {a.resultado_resumen && <p>{a.resultado_resumen}</p>}
          {a.error_mensaje && <p className="warning-text small">{a.error_mensaje}</p>}
          {a.evidencia_ref && <p className="muted small">Evidencia: {a.evidencia_ref}</p>}
          <div className="hallazgo-actions">
            {a.estado === "PENDIENTE_APROBACION" && has("evaluacion.accion.approve") && (
              <>
                <button type="button" className="btn small primary" onClick={() => onAprobar(a.id, true)}>Aprobar</button>
                <button type="button" className="btn small" onClick={() => onAprobar(a.id, false)}>Rechazar</button>
              </>
            )}
            {a.estado === "BORRADOR" && has("evaluacion.accion.request") && (
              <button type="button" className="btn small" onClick={() => onSolicitar(a.id)}>Solicitar</button>
            )}
            {a.detalle_tecnico_url && has("evaluacion.accion.request") && (
              <a href={a.detalle_tecnico_url} className="btn small" target="_blank" rel="noopener noreferrer">Ver detalle técnico en PIIAX</a>
            )}
          </div>
        </article>
      ))}
    </div>
  );
}
