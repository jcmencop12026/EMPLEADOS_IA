import { Link } from "react-router-dom";
import type { CambioAlcance, ContinuidadVista } from "../../api";
import { formatMoney } from "../../lib/comercialLabels";

type Props = {
  vista: ContinuidadVista | null;
  cambios?: CambioAlcance[];
  loading?: boolean;
  onSolicitarCambio?: (solicitud: string) => void;
  onAvanzarCambio?: (cambioId: string, accion: string, extra?: Record<string, unknown>) => void;
  onIniciarCierre?: (motivo: string) => void;
  onConfirmarCierre?: (closureId: string) => void;
  cierreId?: string | null;
  canManage?: boolean;
  canClose?: boolean;
};

export function ContinuidadVistaPanel({
  vista,
  cambios = [],
  loading,
  onSolicitarCambio,
  onAvanzarCambio,
  onIniciarCierre,
  onConfirmarCierre,
  cierreId,
  canManage,
  canClose,
}: Props) {
  if (loading) return <p>Cargando continuidad…</p>;
  if (!vista) return <p className="muted">Sin datos de continuidad.</p>;

  const refs = vista.referencias ?? {};
  const compromiso = vista.compromiso_snapshot as Record<string, unknown> | undefined;
  const contrato = (compromiso?.contrato ?? vista.contratado) as Record<string, unknown> | undefined;
  const finops = (vista.operando as Record<string, unknown> | undefined)?.finops as Record<string, unknown> | undefined;

  return (
    <div className="continuidad-panel">
      <section className="panel compact-panel">
        <h2>Cadena de valor</h2>
        <ol className="continuidad-chain">
          <li>
            <strong>Diagnosticado</strong>
            <span>{(vista.diagnosticado as { titulo?: string })?.titulo ?? "—"}</span>
          </li>
          <li>
            <strong>Prometido</strong>
            <span>{(vista.prometido as { propuesta?: { titulo?: string } })?.propuesta?.titulo ?? "—"}</span>
          </li>
          <li>
            <strong>Contratado</strong>
            <span>
              {contrato?.precio_contratado != null
                ? formatMoney(contrato.precio_contratado as number, (contrato.moneda as string) ?? "USD")
                : "—"}
              {contrato?.modalidad ? ` · ${String(contrato.modalidad)}` : ""}
            </span>
          </li>
          <li>
            <strong>Implementado</strong>
            <span>
              {(vista.implementado as { codigo?: string })?.codigo ?? "—"}
              {(vista.implementado as { estado?: string })?.estado
                ? ` (${(vista.implementado as { estado?: string }).estado})`
                : ""}
            </span>
          </li>
          <li>
            <strong>Operando</strong>
            <span>
              {finops?.presupuesto_operacional != null
                ? `Presupuesto op. ${formatMoney(finops.presupuesto_operacional as number)}`
                : "Sin presupuesto FinOps vinculado"}
            </span>
          </li>
          <li>
            <strong>Proyectado</strong>
            <span>
              {vista.proyectado?.valor_total_esperado != null
                ? formatMoney(vista.proyectado.valor_total_esperado as number)
                : "—"}
            </span>
          </li>
          <li>
            <strong>Resultado real</strong>
            <span>{String((vista.resultado_real as { fuente?: string })?.fuente ?? "Adaptador local")}</span>
          </li>
        </ol>
      </section>

      <section className="panel compact-panel">
        <h3>Referencias canónicas</h3>
        <dl className="detail-dl">
          <dt>Propuesta</dt>
          <dd>
            {refs.proposal_id ? (
              <Link to={`/centro-negocios/propuestas/${refs.proposal_id}`}>{refs.proposal_id}</Link>
            ) : (
              "—"
            )}
          </dd>
          <dt>Contrato</dt>
          <dd>{refs.contract_id ?? "—"}</dd>
          <dt>Proyecto</dt>
          <dd>
            {refs.proyecto_id ? (
              <Link to={`/implementacion/${refs.proyecto_id}`}>{refs.proyecto_id}</Link>
            ) : (
              "—"
            )}
          </dd>
          <dt>Oportunidad</dt>
          <dd>{refs.opportunity_id ?? "—"}</dd>
          <dt>Evaluación</dt>
          <dd>{refs.evaluacion_id ?? "—"}</dd>
        </dl>
      </section>

      {canManage && onSolicitarCambio && (
        <section className="panel compact-panel">
          <h3>Cambios de alcance</h3>
          {cambios.length === 0 ? (
            <p className="muted">Sin solicitudes registradas.</p>
          ) : (
            <ul className="compact-list">
              {cambios.map((c) => (
                <li key={c.id}>
                  <strong>{c.codigo}</strong> — {c.estado}: {c.solicitud}
                  {onAvanzarCambio && c.estado === "SOLICITADO" && (
                    <button type="button" className="btn small" onClick={() => onAvanzarCambio(c.id, "analizar", { analisis: "En revisión" })}>
                      Analizar
                    </button>
                  )}
                  {onAvanzarCambio && c.estado === "EN_ANALISIS" && (
                    <button
                      type="button"
                      className="btn small"
                      onClick={() =>
                        onAvanzarCambio(c.id, "impacto", {
                          impacto: { alcance: "medio", tiempo_dias: 14, costo: 5000 },
                        })
                      }
                    >
                      Evaluar impacto
                    </button>
                  )}
                  {onAvanzarCambio && c.estado === "IMPACTO_EVALUADO" && (
                    <button
                      type="button"
                      className="btn small"
                      onClick={() => onAvanzarCambio(c.id, "decidir", { decision: "Aprobado", aprobado: true })}
                    >
                      Aprobar
                    </button>
                  )}
                </li>
              ))}
            </ul>
          )}
          <button
            type="button"
            className="btn"
            onClick={() => {
              const solicitud = window.prompt("Describa la solicitud de cambio:");
              if (solicitud) onSolicitarCambio(solicitud);
            }}
          >
            Nueva solicitud de cambio
          </button>
        </section>
      )}

      {canClose && refs.contract_id && onIniciarCierre && (
        <section className="panel compact-panel">
          <h3>Cierre / offboarding</h3>
          {!cierreId ? (
            <button
              type="button"
              className="btn"
              onClick={() => {
                const motivo = window.prompt("Motivo de cierre contractual:");
                if (motivo) onIniciarCierre(motivo);
              }}
            >
              Iniciar cierre contractual
            </button>
          ) : (
            <p>
              Cierre en curso ({cierreId})
              {onConfirmarCierre && (
                <button type="button" className="btn primary small" onClick={() => onConfirmarCierre(cierreId)}>
                  Confirmar cierre
                </button>
              )}
            </p>
          )}
        </section>
      )}
    </div>
  );
}
