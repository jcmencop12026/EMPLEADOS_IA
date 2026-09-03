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

const VISTAS: { id: VistaInforme; label: string; desc: string }[] = [
  { id: "ejecutiva", label: "Ejecutiva", desc: "Síntesis, KPIs, alertas, valor y recomendación" },
  { id: "operativa", label: "Operativa", desc: "Proceso, indicadores y desviaciones" },
  { id: "valor", label: "Resultados / Valor", desc: "Antes → Proyectado → Real (etiquetado)" },
  { id: "cliente", label: "Publicable cliente", desc: "Solo contenido autorizado para la empresa" },
];

function fmt(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "number") return v.toLocaleString("es-CO");
  return String(v);
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
  const demoTag = isDemo ? "DEMO — DATOS SIMULADOS" : null;

  const narrativa = useMemo(
    () => ({
      que: "Glosas recurrentes y reprocesos manuales en facturación y cartera.",
      porQue: "Codificación inconsistente y validación documental lenta.",
      significa: "Pérdida de ingresos recuperables y sobrecarga operativa.",
      atencion: "Aprobación pendiente del piloto Empleado IA y documentación incompleta.",
      oportunidad: "Automatización codificación + auditoría documental asistida.",
      valor: fmt(resumen?.estimado ?? resumen?.potencial),
      recomendacion: "Capacitar equipo, desplegar reglas IA y medir antes/proyectado/real trimestral.",
    }),
    [resumen],
  );

  return (
    <div className="cabina-informes-panel">
      <section className="panel compact-panel">
        <h2>Informes EIAAX — experiencia completa</h2>
        <p className="muted small">
          Qué ocurrió → por qué → qué significa → atención → oportunidad → valor → recomendación.
          {demoTag && <> · <strong>{demoTag}</strong></>}
        </p>
        <nav className="tab-bar compact-tabs" aria-label="Vistas de informe">
          {VISTAS.map((v) => (
            <button
              key={v.id}
              type="button"
              className={`tab-btn ${vista === v.id ? "active" : ""}`}
              onClick={() => setVista(v.id)}
              title={v.desc}
            >
              {v.label}
            </button>
          ))}
        </nav>
      </section>

      {loading && <p className="muted">Cargando informes…</p>}

      {!loading && vista === "ejecutiva" && (
        <section className="panel compact-panel informe-vista-ejecutiva">
          <h3 className="section-title">Vista ejecutiva</h3>
          <div className="executive-kpi-strip">
            <div className="executive-kpi"><span>Informes</span><strong>{informes.length}</strong></div>
            <div className="executive-kpi"><span>Indicadores</span><strong>{indicadores.length}</strong></div>
            <div className="executive-kpi"><span>Valor estimado</span><strong>{fmt(resumen?.estimado)}</strong></div>
            <div className="executive-kpi"><span>Potencial</span><strong className="potential-excluded">{fmt(resumen?.potencial)}</strong></div>
          </div>
          <dl className="detail-grid compact">
            <dt>Qué ocurrió</dt><dd>{narrativa.que}</dd>
            <dt>Por qué</dt><dd>{narrativa.porQue}</dd>
            <dt>Requiere atención</dt><dd>{narrativa.atencion}</dd>
            <dt>Recomendación EIAAX</dt><dd>{narrativa.recomendacion}</dd>
          </dl>
          {ultimo && (
            <p className="muted small">
              Último informe: <Link to={`/resultados/informes/${ultimo.id}`}>{ultimo.titulo ?? ultimo.tipo}</Link>
            </p>
          )}
        </section>
      )}

      {!loading && vista === "operativa" && (
        <section className="panel compact-panel">
          <h3 className="section-title">Vista operativa</h3>
          <p className="muted small">Proceso: Facturación / cartera · {entidadNombre ?? "Empresa"}</p>
          {indicadores.length === 0 ? (
            <p className="muted">Sin indicadores operativos registrados.</p>
          ) : (
            <table className="data-table compact-table">
              <thead>
                <tr><th>Indicador</th><th>Antes</th><th>Proyectado</th><th>Real</th><th>Desviación</th></tr>
              </thead>
              <tbody>
                {indicadores.map((ind) => {
                  const antes = Number(ind.antes);
                  const real = ind.real != null ? Number(ind.real) : null;
                  const desv = real != null && !Number.isNaN(antes) ? (real - antes).toLocaleString("es-CO") : "—";
                  return (
                    <tr key={String(ind.id ?? ind.nombre)}>
                      <td>{String(ind.nombre)}</td>
                      <td>{fmt(ind.antes)}</td>
                      <td><span className="tag-proyectado">{fmt(ind.proyectado)}</span></td>
                      <td>{fmt(ind.real)}</td>
                      <td>{desv}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </section>
      )}

      {!loading && vista === "valor" && (
        <section className="panel compact-panel">
          <h3 className="section-title">Resultados y valor</h3>
          <p className="muted small potential-excluded">Proyectado y potencial no se presentan como valor verificado.</p>
          <div className="value-nature-grid compact">
            <div className="value-nature-card verified"><span>Verificado</span><strong>{fmt(resumen?.verificado)}</strong></div>
            <div className="value-nature-card estimated"><span>Estimado</span><strong>{fmt(resumen?.estimado)}</strong></div>
            <div className="value-nature-card potential"><span>Potencial</span><strong>{fmt(resumen?.potencial)}</strong></div>
          </div>
          <p><Link to={`/resultados-inteligencia?expediente_id=${expedienteId}`}>Tablero completo de resultados</Link></p>
        </section>
      )}

      {!loading && vista === "cliente" && (
        <section className="panel compact-panel">
          <h3 className="section-title">Vista publicable para cliente</h3>
          <p className="muted small">Sin costos internos, margen, precio sugerido ni reglas privadas.</p>
          <ul className="compact-list">
            <li>Hallazgos y recomendaciones autorizados para la empresa</li>
            <li>Indicadores antes / proyectado / real visibles según permisos</li>
            <li>Oportunidades de mejora sin economía privada del operador</li>
          </ul>
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
        {comerciales.length > 0 && (
          <p className="muted small">{comerciales.length} programación(es) comercial(es) configurada(s).</p>
        )}
        {plantillas.length > 0 && (
          <p className="muted small">{plantillas.length} plantilla(s) periódica(s).</p>
        )}
      </section>
    </div>
  );
}
