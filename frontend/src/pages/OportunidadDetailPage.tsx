import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import type { OpportunityItem } from "../api";
import {
  activateOpportunity,
  approveOpportunity,
  evaluateOpportunity,
  fetchOpportunity,
  fetchOpportunityTrace,
} from "../api";

type Tab = "resumen" | "evidencia" | "contexto" | "accion" | "equipo" | "trazabilidad" | "finops";

const TABS: { id: Tab; label: string }[] = [
  { id: "resumen", label: "Resumen" },
  { id: "evidencia", label: "Evidencia" },
  { id: "contexto", label: "Contexto" },
  { id: "accion", label: "Siguiente acción" },
  { id: "equipo", label: "Equipo IA" },
  { id: "trazabilidad", label: "Trazabilidad" },
  { id: "finops", label: "FinOps" },
];

export function OportunidadDetailPage() {
  const { opportunityId } = useParams<{ opportunityId: string }>();
  const [opp, setOpp] = useState<OpportunityItem & Record<string, unknown> | null>(null);
  const [trace, setTrace] = useState<Record<string, unknown> | null>(null);
  const [tab, setTab] = useState<Tab>("resumen");
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  function reload() {
    if (!opportunityId) return;
    Promise.all([fetchOpportunity(opportunityId), fetchOpportunityTrace(opportunityId)])
      .then(([o, t]) => { setOpp(o as OpportunityItem & Record<string, unknown>); setTrace(t); })
      .catch((e) => setError(e instanceof Error ? e.message : "Error"));
  }

  useEffect(() => { reload(); }, [opportunityId]);

  async function onEvaluar() {
    if (!opportunityId) return;
    try {
      await evaluateOpportunity(opportunityId);
      setMsg("Evaluación completada");
      reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    }
  }

  async function onAprobar() {
    if (!opportunityId) return;
    try {
      await approveOpportunity(opportunityId, true, "Aprobación desde centro");
      setMsg("Oportunidad aprobada");
      reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    }
  }

  async function onActivar() {
    if (!opportunityId) return;
    try {
      await activateOpportunity(opportunityId);
      setMsg("Oportunidad activada — WorkPlan creado");
      reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    }
  }

  if (!opp) return <div className="ops-page"><p className="muted">Cargando…</p></div>;

  const accion = opp.siguiente_accion as Record<string, unknown> | null;
  const equipo = opp.equipo as Record<string, unknown> | null;

  return (
    <div className="ops-page">
      <header className="page-header">
        <p><Link to="/oportunidades">← Centro de oportunidades</Link></p>
        <h1>{opp.titulo as string}</h1>
        <p className="muted">{opp.codigo as string} · {opp.estado as string} · {opp.dominio as string}</p>
      </header>

      {error && <p className="error">{error}</p>}
      {msg && <p className="success">{msg}</p>}

      <div className="toolbar" style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
        <button type="button" onClick={onEvaluar} title="Re-evaluar pertinencia y prioridad">Evaluar</button>
        <button type="button" onClick={onAprobar} title="Aprobar oportunidad">Aprobar</button>
        <button type="button" onClick={onActivar} title="Activar y crear WorkPlan">Activar</button>
      </div>

      <nav className="tab-bar" style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem", flexWrap: "wrap" }}>
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            className={tab === t.id ? "tab-active" : ""}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <div className="panel">
        {tab === "resumen" && (
          <dl className="detail-grid">
            <dt>Tipo</dt><dd>{opp.tipo as string}</dd>
            <dt>Pertinencia</dt><dd>{opp.pertinencia as string ?? "—"}</dd>
            <dt>Momento</dt><dd>{opp.momento as string ?? "—"}</dd>
            <dt>Prioridad</dt><dd>{opp.prioridad_score != null ? Number(opp.prioridad_score).toFixed(2) : "—"}</dd>
            <dt>Valor potencial</dt><dd>{opp.valor_potencial as number ?? "—"} ({opp.valor_potencial_certidumbre as string})</dd>
            <dt>Valor materializado</dt><dd>{opp.valor_materializado as number ?? "—"}</dd>
            <dt>Confianza</dt><dd>{Number(opp.confianza).toFixed(2)}</dd>
            <dt>Descripción</dt><dd>{(opp.descripcion as string) ?? "—"}</dd>
          </dl>
        )}
        {tab === "evidencia" && (
          <pre>{JSON.stringify(opp.evidencia, null, 2)}</pre>
        )}
        {tab === "contexto" && (
          <pre>{JSON.stringify(opp.contexto, null, 2)}</pre>
        )}
        {tab === "accion" && (
          accion ? <pre>{JSON.stringify(accion, null, 2)}</pre> : <p className="muted">Sin acción definida</p>
        )}
        {tab === "equipo" && (
          equipo ? <pre>{JSON.stringify(equipo, null, 2)}</pre> : <p className="muted">Equipo no asignado</p>
        )}
        {tab === "trazabilidad" && (
          <pre>{JSON.stringify(trace, null, 2)}</pre>
        )}
        {tab === "finops" && (
          <dl className="detail-grid">
            <dt>Referencia FINOPS</dt><dd>{(opp.finops_reference as string) ?? "—"}</dd>
            <dt>WorkPlan</dt><dd>{(opp.work_plan_id as string) ?? "—"}</dd>
            <dt>Atribución</dt><dd>{(opp.atribucion_nivel as string) ?? "—"}</dd>
          </dl>
        )}
      </div>
    </div>
  );
}
