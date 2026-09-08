import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  createPropuestaDesdeExpediente,
  fetchCentroNegociosPipeline,
  type CentroNegociosPipelineItem,
} from "../../api";
import { EspacioExternoAdminPanel } from "../espacioExterno/EspacioExternoAdminPanel";
import { labelProposalStatus } from "../../lib/negocioLabels";
import { CommercialCycle, EmptyState, FormSection } from "../v1";

type Props = {
  expedienteId: string;
  entidadNombre?: string;
};

function stageFromEstado(estado: string): string {
  const map: Record<string, string> = {
    PROSPECTO: "prospecto",
    EVALUACION: "evaluacion",
    PROPUESTA: "propuesta",
    NEGOCIACION: "contrato",
    CONTRATO: "contrato",
    CLIENTE: "cliente",
    OPERACION: "operacion",
  };
  return map[estado] ?? "evaluacion";
}

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
      <FormSection
        title="Comercial y contrato"
        description="Ciclo prospecto → evaluación → oportunidad → propuesta → contrato → cliente → operación"
      >
        {loading && <p className="muted">Cargando estado comercial…</p>}
        {error && <p className="error">{error}</p>}
        {msg && <p className="success">{msg}</p>}

        <CommercialCycle
          currentStage={propuesta ? stageFromEstado(propuesta.estado) : "evaluacion"}
          nextStep={propuesta?.proximo_paso ?? "Generar propuesta desde expediente"}
        />

        {!loading && !propuesta && (
          <EmptyState
            title="Sin propuesta comercial vinculada"
            description="Este expediente aún no tiene propuesta comercial. Genere una desde la evaluación para avanzar hacia contrato y operación."
            action={
              <button type="button" className="btn primary" onClick={() => void onGenerarPropuesta()}>
                Generar propuesta desde expediente
              </button>
            }
          />
        )}

        {propuesta && (
          <>
            <dl className="detail-grid compact">
              <dt>Etapa actual</dt><dd>{labelProposalStatus(propuesta.estado) || propuesta.estado}</dd>
              <dt>Prospecto / entidad</dt><dd>{propuesta.titulo ?? entidadNombre ?? "—"}</dd>
              <dt>Inversión</dt><dd>{propuesta.precio_final != null ? propuesta.precio_final.toLocaleString("es-CO") : "—"}</dd>
              <dt>Próximo paso</dt><dd>{propuesta.proximo_paso ?? "Revisar propuesta con el cliente"}</dd>
              <dt>Oportunidad</dt><dd>{propuesta.opportunity_id ? <Link to={`/oportunidades/${propuesta.opportunity_id}`}>Ver oportunidad</Link> : "—"}</dd>
            </dl>
            <div className="ops-actions">
              <Link className="btn primary small" to={`/centro-negocios/${propuesta.id}`}>Gestionar propuesta</Link>
              <Link className="btn secondary small" to={`/comercial/propuestas/${propuesta.id}`}>Detalle comercial</Link>
            </div>
          </>
        )}
      </FormSection>
      <EspacioExternoAdminPanel expedienteId={expedienteId} />
    </div>
  );
}
