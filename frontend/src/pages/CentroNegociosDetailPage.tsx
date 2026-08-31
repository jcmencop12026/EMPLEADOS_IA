import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  approveNegocioLevel,
  avanzarCambioAlcance,
  confirmarCierreContrato,
  convertirAImplementacion,
  crearCambioAlcance,
  decidirPrecioNegocio,
  fetchCambiosAlcance,
  fetchCentroNegociosDetalle,
  fetchContinuidadVistaPorPropuesta,
  generarPropuestaPdf,
  iniciarCierreContrato,
  openCentroNegociosDocumentPdf,
  registrarNegociacion,
  sincronizarNegocioOportunidad,
  transicionPropuestaNegocio,
  type CambioAlcance,
  type CentroNegociosDetalle,
  type ContinuidadVista,
} from "../api";
import { ContinuidadVistaPanel } from "../components/continuidad/ContinuidadVistaPanel";
import { usePermissions } from "../hooks/usePermissions";
import { formatMoney } from "../lib/comercialLabels";
import { labelApprovalLevel, labelProposalStatus, PRICE_PHASE_LABELS } from "../lib/negocioLabels";

type Tab = "resumen" | "economia" | "versiones" | "aprobaciones" | "negociacion" | "trazabilidad" | "continuidad";

export function CentroNegociosDetailPage() {
  const { proposalId } = useParams<{ proposalId: string }>();
  const { has } = usePermissions();
  const [detail, setDetail] = useState<CentroNegociosDetalle | null>(null);
  const [tab, setTab] = useState<Tab>("resumen");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [vista, setVista] = useState<ContinuidadVista | null>(null);
  const [cambios, setCambios] = useState<CambioAlcance[]>([]);
  const [proyectoId, setProyectoId] = useState<string | null>(null);
  const [contractId, setContractId] = useState<string | null>(null);
  const [cierreId, setCierreId] = useState<string | null>(null);

  function reload() {
    if (!proposalId) return;
    setLoading(true);
    fetchCentroNegociosDetalle(proposalId)
      .then((d) => {
        setDetail(d);
        const neg = d.negocio ?? {};
        setProyectoId((neg.implementacion_proyecto_id as string) ?? null);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Error"))
      .finally(() => setLoading(false));
    if (has("continuidad_comercial.view")) {
      fetchContinuidadVistaPorPropuesta(proposalId)
        .then((v) => {
          setVista(v);
          setContractId(v.referencias?.contract_id ?? null);
          setProyectoId(v.referencias?.proyecto_id ?? null);
        })
        .catch(() => setVista(null));
      fetchCambiosAlcance(proposalId).then(setCambios).catch(() => setCambios([]));
    }
  }

  useEffect(() => {
    reload();
  }, [proposalId]);

  async function onApproveLevel(nivel: string) {
    if (!proposalId) return;
    setBusy(true);
    try {
      await approveNegocioLevel(proposalId, { nivel });
      reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al aprobar");
    } finally {
      setBusy(false);
    }
  }

  async function onPresent() {
    if (!proposalId) return;
    setBusy(true);
    try {
      await transicionPropuestaNegocio(proposalId, { nuevo_estado: "ENVIADA", motivo: "Presentación al cliente" });
      reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo presentar");
    } finally {
      setBusy(false);
    }
  }

  async function onGeneratePdf() {
    if (!proposalId) return;
    setBusy(true);
    try {
      const res = await generarPropuestaPdf(proposalId);
      openCentroNegociosDocumentPdf(res.document_id);
      reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al generar PDF");
    } finally {
      setBusy(false);
    }
  }

  async function onSync() {
    if (!proposalId) return;
    setBusy(true);
    try {
      await sincronizarNegocioOportunidad(proposalId, { direction: "both" });
      reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error de sincronización");
    } finally {
      setBusy(false);
    }
  }

  if (!proposalId) return <p className="error-text">Propuesta no especificada</p>;
  if (loading) return <p>Cargando expediente…</p>;
  if (!detail) return <p className="error-text">{error ?? "Sin datos"}</p>;

  const neg = detail.negocio ?? {};

  return (
    <div className="ops-page">
      <header className="ops-header">
        <Link to="/centro-negocios" className="muted">← Centro de Negocios</Link>
        <h1>{detail.codigo} — {detail.titulo}</h1>
        <p className="muted">
          {labelProposalStatus(detail.estado)} · v{neg.version_actual ?? 1}
          {detail.prospecto ? ` · ${detail.prospecto}` : ""}
        </p>
        <div className="ops-actions">
          {has("negocio.manage") && (
            <>
              <button type="button" className="btn" disabled={busy} onClick={onSync}>Sincronizar oportunidad</button>
              <button type="button" className="btn" disabled={busy} onClick={onGeneratePdf}>Generar PDF</button>
            </>
          )}
          {has("negocio.proposal.present") && detail.estado === "APROBADA" && (
            <button type="button" className="btn primary" disabled={busy} onClick={onPresent}>Presentar</button>
          )}
          {has("negocio.contract") && detail.estado === "ENVIADA" && (
            <button
              type="button"
              className="btn primary"
              disabled={busy}
              onClick={async () => {
                setBusy(true);
                try {
                  const res = await convertirAImplementacion(proposalId) as { proyecto_id?: string };
                  if (res.proyecto_id) setProyectoId(res.proyecto_id);
                  reload();
                } finally {
                  setBusy(false);
                }
              }}
            >
              Contratar e implementar
            </button>
          )}
          {proyectoId && (
            <Link to={`/implementacion/${proyectoId}`} className="btn primary">Ver implementación →</Link>
          )}
          <Link to={`/comercial/propuestas/${proposalId}`} className="btn">Vista comercial →</Link>
        </div>
      </header>

      {error && <p className="error-text">{error}</p>}

      <nav className="tab-nav compact-tabs">
        {(["resumen", "economia", "versiones", "aprobaciones", "negociacion", "trazabilidad", "continuidad"] as Tab[]).map((t) => (
          <button key={t} type="button" className={tab === t ? "active" : ""} onClick={() => setTab(t)}>
            {t === "resumen" ? "Resumen" : t === "economia" ? "Economía" : t === "versiones" ? "Versiones" : t === "aprobaciones" ? "Aprobaciones" : t === "negociacion" ? "Negociación" : t === "trazabilidad" ? "Trazabilidad" : "Continuidad"}
          </button>
        ))}
      </nav>

      {tab === "resumen" && (
        <section className="panel compact-panel">
          <dl className="detail-dl">
            <dt>Origen evaluación</dt><dd>{neg.evaluacion_id ?? "—"}</dd>
            <dt>Oportunidad</dt><dd>{neg.opportunity_id ?? "—"}</dd>
            <dt>Responsable</dt><dd>{neg.responsable_id ?? "—"}</dd>
            <dt>Próximo paso</dt><dd>{neg.proximo_paso ?? "—"}</dd>
            <dt>Modalidad</dt><dd>{neg.modelo_comercial ?? "—"}</dd>
          </dl>
          {detail.documento_cliente && (
            <div className="muted small-note">
              <strong>Resumen:</strong> {String(detail.documento_cliente.resumen_ejecutivo ?? "—")}
            </div>
          )}
        </section>
      )}

      {tab === "economia" && (
        <section className="panel compact-panel">
          <p>Precio autorizado: <strong>{formatMoney(detail.precio_final, detail.currency)}</strong></p>
          <table className="data-table compact-table">
            <thead><tr><th>Fase</th><th>Monto</th><th>Versión</th></tr></thead>
            <tbody>
              {(detail.fases_precio ?? []).map((f, i) => (
                <tr key={i}>
                  <td>{PRICE_PHASE_LABELS[f.fase] ?? f.fase_label}</td>
                  <td>{formatMoney(f.monto, detail.currency)}</td>
                  <td>{f.version_number ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {has("negocio.proposal.approve") && detail.estado === "BORRADOR" && (
            <button
              type="button"
              className="btn"
              disabled={busy}
              onClick={async () => {
                await decidirPrecioNegocio(proposalId, { action: "MODIFICAR", precio_decidido: detail.precio_final ?? 10000 });
                reload();
              }}
            >
              Registrar precio aprobado
            </button>
          )}
        </section>
      )}

      {tab === "versiones" && (
        <section className="panel compact-panel">
          <table className="data-table compact-table">
            <thead><tr><th>Versión</th><th>Estado</th><th>Precio presentado</th><th>PDF</th></tr></thead>
            <tbody>
              {(detail.versiones ?? []).map((v) => (
                <tr key={v.id}>
                  <td>v{v.version_number}</td>
                  <td>{v.estado_label ?? labelProposalStatus(v.estado_comercial)}</td>
                  <td>{formatMoney(v.precio_presentado, detail.currency)}</td>
                  <td>
                    {v.pdf_document_id ? (
                      <button type="button" className="btn small" onClick={() => openCentroNegociosDocumentPdf(v.pdf_document_id!)}>PDF</button>
                    ) : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {tab === "aprobaciones" && (
        <section className="panel compact-panel">
          <table className="data-table compact-table">
            <thead><tr><th>Nivel</th><th>Estado</th><th>Acción</th></tr></thead>
            <tbody>
              {(detail.aprobaciones ?? []).map((a) => (
                <tr key={a.nivel}>
                  <td>{a.nivel_label ?? labelApprovalLevel(a.nivel)}</td>
                  <td>{a.estado}</td>
                  <td>
                    {has("negocio.proposal.approve") && a.estado === "PENDIENTE" && (
                      <button type="button" className="btn small" disabled={busy} onClick={() => onApproveLevel(a.nivel)}>Aprobar</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {tab === "negociacion" && (
        <section className="panel compact-panel">
          {(detail.negociaciones ?? []).length === 0 ? (
            <p className="muted">Sin rondas de negociación registradas.</p>
          ) : (
            <ul>
              {detail.negociaciones!.map((n) => (
                <li key={n.id}>
                  <strong>{n.interlocutor ?? "Cliente"}</strong> — {n.observaciones}
                  {n.cambios_solicitados && <div className="muted">Cambios: {n.cambios_solicitados}</div>}
                </li>
              ))}
            </ul>
          )}
          {has("negocio.manage") && (
            <button
              type="button"
              className="btn"
              disabled={busy}
              onClick={async () => {
                await registrarNegociacion(proposalId, {
                  interlocutor: "Cliente",
                  observaciones: "Solicita ajustes",
                  crear_nueva_version: true,
                });
                reload();
              }}
            >
              Registrar observación y nueva versión
            </button>
          )}
        </section>
      )}

      {tab === "trazabilidad" && (
        <section className="panel compact-panel">
          <h3>Sincronización oportunidad</h3>
          <ul className="muted">
            {(detail.sync_log ?? []).map((s) => (
              <li key={s.id}>{s.direction} · {s.field_name}</li>
            ))}
          </ul>
          {detail.nota_potencial && <p className="small-note">{detail.nota_potencial}</p>}
        </section>
      )}

      {tab === "continuidad" && has("continuidad_comercial.view") && (
        <ContinuidadVistaPanel
          vista={vista}
          cambios={cambios}
          cierreId={cierreId}
          canManage={has("continuidad_comercial.manage")}
          canClose={has("continuidad_comercial.close")}
          onSolicitarCambio={async (solicitud) => {
            if (!proposalId) return;
            await crearCambioAlcance({
              proposal_id: proposalId,
              proyecto_id: proyectoId,
              contract_id: contractId,
              solicitud,
            });
            reload();
          }}
          onAvanzarCambio={async (cambioId, accion, extra) => {
            await avanzarCambioAlcance(cambioId, { accion, ...extra });
            reload();
          }}
          onIniciarCierre={async (motivo) => {
            if (!contractId) return;
            const cierre = await iniciarCierreContrato(contractId, { motivo, pendientes: [] });
            setCierreId(cierre.id);
            reload();
          }}
          onConfirmarCierre={async (id) => {
            await confirmarCierreContrato(id);
            reload();
          }}
        />
      )}
    </div>
  );
}
