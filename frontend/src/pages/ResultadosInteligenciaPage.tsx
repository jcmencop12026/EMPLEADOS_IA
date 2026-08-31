import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  fetchAntesProyectadoReal,
  fetchInformesImpacto,
  fetchResultadosIndicadores,
  generarInformeImpacto,
  type InformeImpacto,
  type ResultadoIndicador,
} from "../api";
import { ContextualHelp } from "../components/ContextualHelp";
import { EiaaxTable, type EiaaxColumn } from "../components/EiaaxTable";
import { usePermissions } from "../hooks/usePermissions";
import { HELP_ANTES_PROYECTADO_REAL, HELP_RESULTADOS_HUB } from "../lib/resultadosHelp";

function fmtVal(v: number | null | undefined, unidad?: string): string {
  if (v == null) return "—";
  return `${v.toLocaleString("es-CO")}${unidad ? ` ${unidad}` : ""}`;
}

export function ResultadosInteligenciaPage() {
  const { has } = usePermissions();
  const [params] = useSearchParams();
  const expedienteFilter = params.get("expediente_id") ?? "";
  const [indicadores, setIndicadores] = useState<ResultadoIndicador[]>([]);
  const [informes, setInformes] = useState<InformeImpacto[]>([]);
  const [apr, setApr] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  function load() {
    setLoading(true);
    const qs = expedienteFilter ? `expediente_id=${expedienteFilter}` : "";
    Promise.all([
      fetchResultadosIndicadores(qs || undefined),
      fetchInformesImpacto(expedienteFilter || undefined),
      fetchAntesProyectadoReal(expedienteFilter || undefined),
    ])
      .then(([ind, inf, a]) => {
        setIndicadores(ind.items);
        setInformes(inf.items);
        setApr(a);
        setError(null);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar"))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
  }, [expedienteFilter]);

  const columns = useMemo<EiaaxColumn<ResultadoIndicador>[]>(
    () => [
      { key: "nombre", label: "Indicador", sortable: true, getValue: (r) => r.nombre },
      {
        key: "antes",
        label: "ANTES",
        sortable: true,
        getValue: (r) => r.antes,
        render: (r) => <span className="badge estado-recibido">{fmtVal(r.antes, r.unidad)}</span>,
      },
      {
        key: "proyectado",
        label: "PROYECTADO",
        sortable: true,
        getValue: (r) => r.proyectado,
        render: (r) =>
          r.proyectado != null ? (
            <span className="tag-proyectado" title="Proyección — no es resultado conseguido">
              {fmtVal(r.proyectado, r.unidad)}
            </span>
          ) : (
            "—"
          ),
      },
      {
        key: "real",
        label: "REAL",
        sortable: true,
        getValue: (r) => r.real,
        render: (r) =>
          r.real != null ? (
            <strong>{fmtVal(r.real, r.unidad)}</strong>
          ) : r.sin_medicion_posterior ? (
            <span className="muted small">Sin medición posterior</span>
          ) : (
            "—"
          ),
      },
      { key: "tipo_analitica", label: "Analítica", sortable: true, getValue: (r) => r.tipo_analitica },
      { key: "confianza", label: "Confianza", sortable: true, getValue: (r) => r.confianza },
      {
        key: "expediente_id",
        label: "Expediente",
        render: (r) =>
          r.expediente_id ? (
            <Link to={`/evaluaciones/${r.expediente_id}`}>Ver consola</Link>
          ) : (
            "—"
          ),
      },
    ],
    [],
  );

  async function onGenerarInforme() {
    if (!expedienteFilter) {
      setError("Seleccione un expediente (parámetro expediente_id) para generar informe.");
      return;
    }
    try {
      const inf = await generarInformeImpacto(expedienteFilter);
      setMsg(`Informe generado: ${inf.titulo}`);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo generar el informe");
    }
  }

  return (
    <div className="ops-page">
      <header className="page-header">
        <div className="page-header-row">
          <div>
            <h1>Inteligencia de resultados</h1>
            <p className="muted">Indicadores dinámicos, impacto medido y informes narrativos EIAAX</p>
          </div>
          <ContextualHelp content={HELP_RESULTADOS_HUB} />
        </div>
      </header>

      {error && <p className="error">{error}</p>}
      {msg && <p className="success">{msg}</p>}

      <div className="panel compact-panel filters-row">
        {expedienteFilter && (
          <span className="muted">
            Filtrado por expediente ·{" "}
            <Link to={`/evaluaciones/${expedienteFilter}`}>Abrir consola</Link>
          </span>
        )}
        {has("resultados.informe.generate") && expedienteFilter && (
          <button type="button" className="btn primary" onClick={onGenerarInforme}>
            Generar informe de impacto
          </button>
        )}
        <Link to="/evaluaciones" className="btn">
          Evaluaciones EIAAX
        </Link>
      </div>

      <section className="panel compact-panel">
        <div className="page-header-row">
          <h2>Indicadores</h2>
          <ContextualHelp content={HELP_ANTES_PROYECTADO_REAL} label="ANTES/PROY/REAL" />
        </div>
        <EiaaxTable
          columns={columns}
          data={indicadores}
          rowKey={(r) => r.id}
          loading={loading}
          prefsKey="resultados_indicadores_v1"
          searchPlaceholder="Buscar indicador…"
          searchKeys={["nombre"]}
          emptyMessage="Sin indicadores. Regístrelos desde un expediente o sincronice desde línea base."
          defaultSortKey="nombre"
        />
      </section>

      {informes.length > 0 && (
        <section className="panel compact-panel">
          <h2>Informes de impacto</h2>
          <ul className="vista-entidad-list compact">
            {informes.map((inf) => (
              <li key={inf.id}>
                <Link to={`/resultados/informes/${inf.id}`}>
                  {inf.titulo} — v{inf.version} ({inf.visibilidad})
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      {apr && (
        <p className="muted small">{String(apr.nota ?? "")}</p>
      )}
    </div>
  );
}
