import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  fetchCommCentroResumen,
  fetchEvaluacionImpacto,
  fetchInformesComercialesConfig,
  fetchInformesImpacto,
  fetchInformesPeriodicosPlantillas,
  type CommCentroResumen,
  type InformeComercialConfig,
  type InformeImpacto,
} from "../../api";

type Props = {
  expedienteId: string;
  entidadNombre?: string;
  isDemo?: boolean;
};

type VistaInforme = "ejecutiva" | "operativa" | "valor" | "cliente";

const VISTAS: { id: VistaInforme; label: string; desc: string; destinatario: string }[] = [
  { id: "ejecutiva", label: "Ejecutiva", desc: "Síntesis, KPIs, alertas, valor y recomendación", destinatario: "Dirección / gerencia" },
  { id: "operativa", label: "Operativa", desc: "Proceso, indicadores y desviaciones", destinatario: "Jefes de proceso / operaciones" },
  { id: "valor", label: "Resultados / Valor", desc: "Antes → Proyectado → Real (etiquetado)", destinatario: "Finanzas / valoración" },
  { id: "cliente", label: "Publicable cliente", desc: "Solo contenido autorizado para la empresa", destinatario: "Empresa cliente (vista entidad)" },
];

function fmt(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "number") return v.toLocaleString("es-CO");
  return String(v);
}

function demoMonto(block: unknown): string {
  if (!block || typeof block !== "object") return "—";
  const b = block as { monto?: number; etiqueta?: string };
  if (!b.monto) return "—";
  return `${b.etiqueta ?? ""}: $${Number(b.monto).toLocaleString("es-CO")} COP`.trim();
}

export function CabinaInformesPanel({ expedienteId, entidadNombre, isDemo }: Props) {
  const [vista, setVista] = useState<VistaInforme>("ejecutiva");
  const [informes, setInformes] = useState<InformeImpacto[]>([]);
  const [comerciales, setComerciales] = useState<InformeComercialConfig[]>([]);
  const [plantillas, setPlantillas] = useState<Array<Record<string, unknown>>>([]);
  const [comm, setComm] = useState<CommCentroResumen | null>(null);
  const [impacto, setImpacto] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetchInformesImpacto(expedienteId).then((r) => setInformes(r.items)),
      fetchInformesComercialesConfig().then((r) => setComerciales(r.items)).catch(() => undefined),
      fetchInformesPeriodicosPlantillas().then((r) => setPlantillas(r.plantillas)).catch(() => undefined),
      fetchCommCentroResumen().then(setComm).catch(() => undefined),
      fetchEvaluacionImpacto(expedienteId).then(setImpacto).catch(() => undefined),
    ]).finally(() => setLoading(false));
  }, [expedienteId]);

  const ultimo = informes[0];
  const indicadores = (impacto?.indicadores as Array<Record<string, unknown>> | undefined) ?? [];
  const resumen = impacto?.resumen as Record<string, unknown> | undefined;
  const interpretacion = impacto?.interpretacion as Record<string, unknown> | undefined;
  const esDemo = Boolean(isDemo || resumen?.es_demo);
  const demoTag = esDemo ? "DEMO — DATOS SIMULADOS" : null;

  const narrativa = useMemo(
    () => ({
      que: String(interpretacion?.que_ocurrio ?? "Glosas recurrentes y reprocesos manuales en facturación y cartera."),
      porQue: String(interpretacion?.por_que ?? "Codificación inconsistente y validación documental lenta."),
      significa: String(interpretacion?.que_significa ?? "Pérdida de ingresos recuperables y sobrecarga operativa."),
      atencion: String(interpretacion?.requiere_atencion ?? "Aprobación pendiente del piloto y documentación incompleta."),
      oportunidad: String(interpretacion?.oportunidad ?? "Automatización codificación + auditoría documental asistida."),
      valor: esDemo
        ? `${demoMonto(resumen?.estimado)} · ${demoMonto(resumen?.potencial)}`
        : fmt((resumen as Record<string, unknown>)?.estimado ?? (resumen as Record<string, unknown>)?.potencial),
      recomendacion: String(interpretacion?.recomendacion ?? "Capacitar equipo, desplegar reglas IA y medir trimestralmente."),
    }),
    [interpretacion, resumen, esDemo],
  );

  const vistaMeta = VISTAS.find((v) => v.id === vista);

  return (
    <div className="cabina-informes-panel">
      <section className="panel compact-panel">
        <h2>Informes EIAAX — experiencia completa</h2>
        <p className="muted small">
          Qué ocurrió → por qué → qué significa → atención → oportunidad → valor → recomendación.
          {demoTag && <> · <strong className="demo-banner-inline">{demoTag}</strong></>}
        </p>
        <nav className="tab-bar compact-tabs" aria-label="Vistas de informe">
          {VISTAS.map((v) => (
            <button
              key={v.id}
              type="button"
              className={`tab-btn ${vista === v.id ? "active" : ""}`}
              onClick={() => setVista(v.id)}
              title={`${v.desc} · Destinatario: ${v.destinatario}`}
            >
              {v.label}
            </button>
          ))}
        </nav>
        {vistaMeta && (
          <p className="muted small">
            <strong>Destinatario:</strong> {vistaMeta.destinatario} · {vistaMeta.desc}
          </p>
        )}
      </section>

      {loading && <p className="muted">Cargando informes…</p>}

      {!loading && vista === "ejecutiva" && (
        <section className="panel compact-panel informe-vista-ejecutiva">
          <h3 className="section-title">Vista ejecutiva</h3>
          {esDemo && <p className="demo-banner" role="status">{demoTag}</p>}
          <div className="executive-kpi-strip">
            <div className="executive-kpi"><span>Informes</span><strong>{informes.length}</strong></div>
            <div className="executive-kpi"><span>Indicadores</span><strong>{indicadores.length}</strong></div>
            <div className="executive-kpi"><span>Alertas</span><strong>1</strong></div>
            <div className="executive-kpi"><span>Valor {esDemo ? "simulado" : "estimado"}</span><strong>{esDemo ? demoMonto(resumen?.estimado) : fmt(resumen?.estimado)}</strong></div>
          </div>
          <dl className="detail-grid compact">
            <dt>Qué ocurrió</dt><dd>{narrativa.que}</dd>
            <dt>Por qué</dt><dd>{narrativa.porQue}</dd>
            <dt>Qué significa</dt><dd>{narrativa.significa}</dd>
            <dt>Requiere atención</dt><dd>{narrativa.atencion}</dd>
            <dt>Oportunidad</dt><dd>{narrativa.oportunidad}</dd>
            <dt>Valor</dt><dd>{narrativa.valor}</dd>
            <dt>Recomendación EIAAX</dt><dd>{narrativa.recomendacion}</dd>
          </dl>
          <p className="muted small"><strong>Omite:</strong> costos internos, margen, prompts, reglas privadas.</p>
          {ultimo && (
            <p className="muted small">
              Acción: <Link to={`/resultados/informes/${ultimo.id}`}>Abrir último informe</Link>
            </p>
          )}
        </section>
      )}

      {!loading && vista === "operativa" && (
        <section className="panel compact-panel informe-vista-operativa">
          <h3 className="section-title">Vista operativa</h3>
          <p className="muted small">Proceso: Facturación / cartera · {entidadNombre ?? "Empresa"}</p>
          <p className="muted small"><strong>Muestra:</strong> indicadores, desviaciones, evolución antes/proyectado/real.</p>
          <p className="muted small"><strong>Omite:</strong> economía privada del operador y scoring interno.</p>
          {indicadores.length === 0 ? (
            <p className="muted">Sin indicadores operativos registrados.</p>
          ) : (
            <table className="data-table compact-table">
              <thead>
                <tr><th>Indicador</th><th>Antes</th><th>Proyectado</th><th>Real</th><th>Desviación</th><th>Alerta</th></tr>
              </thead>
              <tbody>
                {indicadores.map((ind) => {
                  const antes = Number(ind.antes);
                  const real = ind.real != null ? Number(ind.real) : null;
                  const desv = real != null && !Number.isNaN(antes) ? (real - antes).toLocaleString("es-CO") : "—";
                  const alerta = real != null && antes > 0 && real > antes * 1.1 ? "Desviación alta" : "—";
                  return (
                    <tr key={String(ind.id ?? ind.nombre)}>
                      <td>{String(ind.nombre)}</td>
                      <td>{fmt(ind.antes)}</td>
                      <td><span className="tag-proyectado">{fmt(ind.proyectado)}</span></td>
                      <td>{fmt(ind.real)}</td>
                      <td>{desv}</td>
                      <td>{alerta}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
          <p className="muted small">Acción: <Link to={`/evaluaciones/${expedienteId}?tab=resultados`}>Profundizar en resultados</Link></p>
        </section>
      )}

      {!loading && vista === "valor" && (
        <section className="panel compact-panel informe-vista-valor">
          <h3 className="section-title">Resultados y valor</h3>
          {esDemo && (
            <p className="demo-banner" role="status">
              {demoTag} — la tarjeta «Simulación verificado» ilustra un futuro resultado, no una medición real.
            </p>
          )}
          <div className="value-nature-grid compact">
            {esDemo ? (
              <>
                <div className="value-nature-card estimated"><span>Simulación verificado</span><strong>{demoMonto(resumen?.simulacion_verificado)}</strong></div>
                <div className="value-nature-card estimated"><span>Estimado</span><strong>{demoMonto(resumen?.estimado)}</strong></div>
                <div className="value-nature-card potential"><span>Potencial</span><strong>{demoMonto(resumen?.potencial)}</strong></div>
              </>
            ) : (
              <>
                <div className="value-nature-card verified"><span>Verificado</span><strong>{fmt(resumen?.verificado)}</strong></div>
                <div className="value-nature-card estimated"><span>Estimado</span><strong>{fmt(resumen?.estimado)}</strong></div>
                <div className="value-nature-card potential"><span>Potencial</span><strong>{fmt(resumen?.potencial)}</strong></div>
              </>
            )}
          </div>
          <dl className="detail-grid compact">
            <dt>Qué ocurrió</dt><dd>{narrativa.que}</dd>
            <dt>Por qué importa</dt><dd>{narrativa.porQue}</dd>
            <dt>Recomendación</dt><dd>{narrativa.recomendacion}</dd>
          </dl>
          <p><Link to={`/resultados-inteligencia?expediente_id=${expedienteId}`}>Tablero completo de resultados</Link></p>
        </section>
      )}

      {!loading && vista === "cliente" && (
        <section className="panel compact-panel informe-vista-cliente">
          <h3 className="section-title">Vista publicable para cliente</h3>
          <p className="muted small"><strong>Destinatario:</strong> empresa cliente · solo contenido autorizado.</p>
          {esDemo && <p className="demo-banner">{demoTag}</p>}
          <dl className="detail-grid compact">
            <dt>Hallazgos publicables</dt>
            <dd>Glosas recurrentes, reprocesos manuales y oportunidad de automatización (según visibilidad).</dd>
            <dt>Indicadores autorizados</dt>
            <dd>{indicadores.length} indicador(es) antes/proyectado/real visibles según permisos.</dd>
            <dt>Valor publicable</dt>
            <dd>
              {esDemo
                ? `${demoMonto(resumen?.estimado)} · ${demoMonto(resumen?.potencial)} (simulado)`
                : fmt(resumen?.estimado)}
            </dd>
            <dt>Recomendación</dt>
            <dd>{narrativa.recomendacion}</dd>
          </dl>
          <p className="muted small"><strong>Omite explícitamente:</strong> costos internos, margen, precio sugerido, prompts, reglas privadas, scoring interno.</p>
          <div className="ops-actions">
            <Link to={`/evaluaciones/${expedienteId}?tab=vista-empresa`} className="btn secondary small">Previsualizar vista empresa</Link>
            <Link to={isDemo ? `/demo/presentacion/${expedienteId}` : `/presentacion/${expedienteId}`} className="btn primary small">Presentar en reunión</Link>
          </div>
        </section>
      )}

      <section className="panel compact-panel">
        <div className="ops-actions">
          <Link className="btn primary small" to={isDemo ? `/demo/presentacion/${expedienteId}` : `/presentacion/${expedienteId}`}>Presentación</Link>
          <Link className="btn secondary small" to={`/resultados-inteligencia?expediente_id=${expedienteId}`}>Informes de impacto</Link>
          <Link className="btn secondary small" to="/comunicaciones">Comunicaciones</Link>
        </div>
        {comm && (
          <p className="muted small">
            Comunicaciones: {comm.enviadas ?? 0} enviados · {comm.pendientes ?? 0} pendientes
          </p>
        )}
      </section>
    </div>
  );
}
