import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  createPropuestaDesdeExpediente,
  fetchCentroNegociosPipeline,
  type CentroNegociosPipelineItem,
} from "../../api";
import { EspacioExternoAdminPanel } from "../espacioExterno/EspacioExternoAdminPanel";
import { labelProposalStatus } from "../../lib/negocioLabels";

type Props = {
  expedienteId: string;
  entidadNombre?: string;
};

export function CabinaContratoPanel({ expedienteId, entidadNombre }: Props) {
  const [propuesta, setPropuesta] = useState<CentroNegociosPipelineItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    fetchCentroNegociosPipeline()
      .then((items) => {
        const match = items.find((p) => p.evaluacion_id === expedienteId) ?? null;
        setPropuesta(match);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar comercial"))
      .finally(() => setLoading(false));
  }, [expedienteId]);

  async function onGenerarPropuesta() {
    setError(null);
    setMsg(null);
    try {
      const r = await createPropuestaDesdeExpediente({ evaluacion_id: expedienteId });
      setMsg("Propuesta comercial generada desde el expediente.");
      const proposalId = String((r as Record<string, unknown>).proposal_id ?? (r as Record<string, unknown>).id ?? "");
      if (proposalId) {
        const items = await fetchCentroNegociosPipeline();
        setPropuesta(items.find((p) => p.id === proposalId) ?? items.find((p) => p.evaluacion_id === expedienteId) ?? null);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo generar la propuesta");
    }
  }

  return (
    <div className="cabina-contrato-panel">
      <section className="panel compact-panel">
        <h2>Comercial y contrato</h2>
        <p className="muted small">
          Ciclo DEMO → PROSPECTO → EVALUACIÓN → OPORTUNIDAD → PROPUESTA → CONTRATO → CLIENTE → OPERACIÓN.
          Reutiliza el expediente existente sin duplicar entidades.
        </p>
        {loading && <p className="muted">Cargando estado comercial…</p>}
        {error && <p className="error">{error}</p>}
        {msg && <p className="success">{msg}</p>}
        {!loading && !propuesta && (
          <div className="empty-inline">
            <p className="muted">No hay propuesta comercial vinculada a este expediente.</p>
            <button type="button" className="btn primary small" onClick={() => void onGenerarPropuesta()}>
              Generar propuesta desde expediente
            </button>
          </div>
        )}
        {propuesta && (
          <>
            <dl className="detail-grid compact">
              <dt>Etapa</dt><dd>{labelProposalStatus(propuesta.estado) || propuesta.estado}</dd>
                <dt>Prospecto / entidad</dt><dd>{propuesta.titulo ?? entidadNombre ?? "—"}</dd>
              <dt>Inversión</dt><dd>{propuesta.precio_final != null ? propuesta.precio_final.toLocaleString("es-CO") : "—"}</dd>
              <dt>Próximo paso</dt><dd>{propuesta.proximo_paso ?? "Revisar propuesta"}</dd>
              <dt>Oportunidad</dt><dd>{propuesta.opportunity_id ? <Link to={`/oportunidades/${propuesta.opportunity_id}`}>Ver</Link> : "—"}</dd>
            </dl>
            <div className="ops-actions">
              <Link className="btn primary small" to={`/centro-negocios/${propuesta.id}`}>Gestionar propuesta</Link>
              <Link className="btn secondary small" to={`/comercial/propuestas/${propuesta.id}`}>Detalle comercial</Link>
            </div>
          </>
        )}
      </section>
      <EspacioExternoAdminPanel expedienteId={expedienteId} />
    </div>
  );
}
