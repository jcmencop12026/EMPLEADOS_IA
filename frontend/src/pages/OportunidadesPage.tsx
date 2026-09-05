import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import type { OpportunityItem, OpportunitySummary } from "../api";
import { fetchOpportunities, fetchOpportunitySummary, prioritizeOpportunities } from "../api";
import { EiaaxTable, type EiaaxColumn } from "../components/EiaaxTable";
import { KpiStrip, PageHeader } from "../components/v1";
import { usePermissions } from "../hooks/usePermissions";
import {
  formatPrioridad,
  labelEstadoOportunidad,
  labelTipoOportunidad,
} from "../lib/oportunidadLabels";

const ESTADOS_FILTRO = [
  "", "DETECTADA", "EN_EVALUACION", "PRIORIZADA", "PROPUESTA", "PENDIENTE_APROBACION",
  "APROBADA", "EN_EJECUCION", "EN_SEGUIMIENTO", "MATERIALIZADA", "CERRADA", "DESCARTADA",
  "DATOS_INSUFICIENTES", "FALLIDA",
] as const;

function estadoLabel(e: string) { return labelEstadoOportunidad(e); }

function formatMoney(v: number | null): string {
  if (v == null) return "—";
  return new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(v);
}

export function OportunidadesPage() {
  const { has } = usePermissions();
  const [items, setItems] = useState<OpportunityItem[]>([]);
  const [summary, setSummary] = useState<OpportunitySummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState<string | null>(null);
  const [filtroEstado, setFiltroEstado] = useState("");
  const [filtroDominio, setFiltroDominio] = useState("");

  useEffect(() => {
    const params = new URLSearchParams();
    if (filtroEstado) params.set("estado", filtroEstado);
    if (filtroDominio) params.set("dominio", filtroDominio);
    setLoading(true);
    Promise.all([
      fetchOpportunities(params.toString()),
      fetchOpportunitySummary(),
    ])
      .then(([list, sum]) => {
        setItems(list.items);
        setSummary(sum);
        setError(null);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar oportunidades"))
      .finally(() => setLoading(false));
  }, [filtroEstado, filtroDominio]);

  async function onPriorizar() {
    try {
      await prioritizeOpportunities();
      setMsg("Priorización global actualizada");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al priorizar");
    }
  }

  const columns = useMemo<EiaaxColumn<OpportunityItem>[]>(() => [
    { key: "titulo", label: "Oportunidad", sortable: true, getValue: (i) => i.titulo, render: (i) => (
      <span>
        <strong>{i.titulo}</strong>
        <span className="muted small"> · {i.codigo}</span>
      </span>
    ) },
    { key: "tipo", label: "Tipo", sortable: true, getValue: (i) => i.tipo ?? "", render: (i) => labelTipoOportunidad(i.tipo) },
    { key: "dominio", label: "Dominio", sortable: true, getValue: (i) => i.dominio ?? "" },
    { key: "estado", label: "Estado", sortable: true, getValue: (i) => i.estado, render: (i) => estadoLabel(i.estado) },
    { key: "prioridad_score", label: "Prioridad", sortable: true, getValue: (i) => i.prioridad_score ?? 0, render: (i) => formatPrioridad(i.prioridad_score != null ? Number(i.prioridad_score) : null) },
    { key: "valor_potencial", label: "Valor potencial", sortable: true, getValue: (i) => i.valor_potencial ?? 0, render: (i) => formatMoney(i.valor_potencial) },
    { key: "fecha_deteccion", label: "Fecha", sortable: true, getValue: (i) => i.fecha_deteccion ?? "", render: (i) => (i.fecha_deteccion ? new Date(i.fecha_deteccion).toLocaleDateString("es-CO") : "—") },
    {
      key: "actions",
      label: "Acciones",
      render: (i) => <Link to={`/oportunidades/${i.id}`} onClick={(e) => e.stopPropagation()}>Abrir oportunidad</Link>,
    },
  ], []);

  const filtersSlot = (
    <>
      <select value={filtroEstado} onChange={(e) => setFiltroEstado(e.target.value)} title="Filtrar por estado">
        <option value="">Todos los estados</option>
        {ESTADOS_FILTRO.filter(Boolean).map((e) => (
          <option key={e} value={e}>{estadoLabel(e)}</option>
        ))}
      </select>
      <select value={filtroDominio} onChange={(e) => setFiltroDominio(e.target.value)} title="Filtrar por dominio">
        <option value="">Todos los dominios</option>
        <option value="administrativo">Administrativo</option>
        <option value="comercial">Comercial</option>
        <option value="financiero">Financiero</option>
        <option value="cumplimiento">Cumplimiento</option>
        <option value="salud">Salud</option>
      </select>
    </>
  );

  const toolbarSlot = has("oportunidades.evaluate") ? (
    <button type="button" onClick={onPriorizar} title="Recalcular priorización global">Priorizar</button>
  ) : null;

  return (
    <div className="ops-page">
      <PageHeader
        title="Centro de oportunidades"
        subtitle="Inteligencia proactiva — detección, priorización y materialización de valor"
        eyebrow="Oportunidades"
      />

      {error && <p className="error">{error}</p>}
      {msg && <p className="success">{msg}</p>}
      {loading && <p className="muted">Cargando oportunidades…</p>}

      {summary && (
        <KpiStrip
          title="Resumen de inteligencia"
          items={[
            { id: "det", label: "Detectadas", value: summary.oportunidades_detectadas },
            { id: "pend", label: "Pendientes", value: summary.pendientes_aprobacion ?? summary.pertinentes },
            { id: "act", label: "Activadas", value: summary.activadas },
            { id: "mat", label: "Materializadas", value: summary.materializadas, tone: "success" },
            { id: "vp", label: "Valor potencial", value: formatMoney(summary.valor_potencial_total), tone: "value" },
            { id: "vm", label: "Valor materializado", value: formatMoney(summary.valor_materializado_total), tone: "value" },
            { id: "ap", label: "Pend. aprobación", value: summary.pendientes_aprobacion, tone: "attention" },
          ]}
        />
      )}

      <div className="panel">
        <EiaaxTable
          columns={columns}
          data={items}
          rowKey={(i) => i.id}
          loading={loading}
          prefsKey="oportunidades-list"
          searchPlaceholder="Buscar oportunidad…"
          filtersSlot={filtersSlot}
          toolbarSlot={toolbarSlot}
          emptyMessage="No hay oportunidades que coincidan con los filtros"
        />
      </div>
    </div>
  );
}
