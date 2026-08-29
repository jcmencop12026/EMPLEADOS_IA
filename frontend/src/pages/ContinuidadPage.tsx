import { useEffect, useState } from "react";
import type { ContinuidadTablero } from "../api";
import { fetchContinuidadTablero } from "../api";
import { formatContinuityEvent } from "../lib/uiTerms";

type TabId =
  | "tablero"
  | "servicios"
  | "planes"
  | "respaldos"
  | "incidentes"
  | "disponibilidad"
  | "pruebas"
  | "procedimientos";

const TABS: { id: TabId; label: string }[] = [
  { id: "tablero", label: "Tablero" },
  { id: "servicios", label: "Servicios críticos" },
  { id: "planes", label: "Planes" },
  { id: "respaldos", label: "Respaldos" },
  { id: "incidentes", label: "Incidentes" },
  { id: "disponibilidad", label: "Disponibilidad" },
  { id: "pruebas", label: "Pruebas" },
  { id: "procedimientos", label: "Procedimientos de recuperación" },
];

export function ContinuidadPage() {
  const [tab, setTab] = useState<TabId>("tablero");
  const [data, setData] = useState<ContinuidadTablero | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchContinuidadTablero()
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar continuidad"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Continuidad operativa</h1>
          <p className="muted">
            Administración de servicios críticos, respaldos, incidentes, RTO/RPO y planes de recuperación.
            Un registro no implica que exista un respaldo real hasta su verificación.
          </p>
        </div>
      </header>

      {error && <div className="alert alert-error">{error}</div>}

      <nav className="tabs" aria-label="Secciones de continuidad">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            className={tab === t.id ? "tab active" : "tab"}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {loading ? (
        <p className="muted">Cargando…</p>
      ) : !data ? (
        <p className="muted">Sin datos de continuidad.</p>
      ) : (
        <section className="card">
          {tab === "tablero" && (
            <div className="grid-2">
              <div>
                <h2>Resumen</h2>
                <dl className="kv-list">
                  <dt>Incidentes abiertos</dt>
                  <dd>{data.incidentes_abiertos}</dd>
                  <dt>Respaldos fallidos</dt>
                  <dd>{data.backups_fallidos}</dd>
                  <dt>Restauraciones verificadas</dt>
                  <dd>{data.restauraciones_verificadas}</dd>
                  <dt>Acciones pendientes</dt>
                  <dd>{data.acciones_pendientes}</dd>
                </dl>
              </div>
              <div>
                <h2>Alertas recientes</h2>
                {data.alertas.length === 0 ? (
                  <p className="muted">Sin alertas activas.</p>
                ) : (
                  <ul>
                    {data.alertas.map((a, i) => (
                      <li key={`${a.tipo}-${i}`}>
                        <strong>{formatContinuityEvent(a.tipo)}</strong>: {a.mensaje}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          )}

          {tab === "servicios" && (
            <>
              <h2>Servicios críticos</h2>
              <p className="muted">
                RTO: objetivo de tiempo de recuperación. RPO: objetivo de punto de recuperación (pérdida máxima de datos).
              </p>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Código</th>
                    <th>Nombre</th>
                    <th>Criticidad</th>
                    <th>Estado</th>
                    <th>RTO</th>
                    <th>RPO</th>
                  </tr>
                </thead>
                <tbody>
                  {data.servicios_criticos.map((s) => (
                    <tr key={s.id}>
                      <td>{s.codigo}</td>
                      <td>{s.nombre}</td>
                      <td>{s.criticidad}</td>
                      <td>{s.estado_operacional}</td>
                      <td>
                        {s.rto_valor != null ? `${s.rto_valor} ${s.rto_unidad ?? ""}` : "—"}
                      </td>
                      <td>
                        {s.rpo_valor != null ? `${s.rpo_valor} ${s.rpo_unidad ?? ""}` : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}

          {tab === "planes" && (
            <>
              <h2>Planes de continuidad</h2>
              <p className="muted">Planes configurables con alcance, RTO/RPO y estado de revisión.</p>
              <p className="muted">Use la API para crear y activar planes de contingencia.</p>
            </>
          )}

          {tab === "respaldos" && (
            <>
              <h2>Respaldos</h2>
              <p className="muted">
                Estados: PROGRAMADO → EJECUTADO → VERIFICADO → RESTAURADO_EN_PRUEBA. No confundir registro con respaldo real.
              </p>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Recurso</th>
                    <th>Resultado</th>
                    <th>Estado registro</th>
                  </tr>
                </thead>
                <tbody>
                  {data.backups_recientes.map((b, i) => (
                    <tr key={`${b.recurso}-${i}`}>
                      <td>{b.recurso}</td>
                      <td>{b.resultado}</td>
                      <td>{b.estado_registro}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}

          {tab === "incidentes" && (
            <>
              <h2>Incidentes operativos</h2>
              <p className="muted">Ciclo: detectado → confirmado → contención → recuperación → monitoreo → resuelto → cerrado.</p>
              <p>
                <strong>Abiertos:</strong> {data.incidentes_abiertos}
              </p>
            </>
          )}

          {tab === "disponibilidad" && (
            <>
              <h2>Disponibilidad y SLA/SLO</h2>
              <p className="muted">
                Indicadores por período. Los objetivos SLA/SLO se distinguen de lo medido; no se promete SLA sin evidencia.
              </p>
              <p>
                <strong>Servicios degradados:</strong> {data.servicios_degradados.length}
              </p>
            </>
          )}

          {tab === "pruebas" && (
            <>
              <h2>Pruebas de continuidad</h2>
              <p className="muted">
                Ejercicios: simulación, prueba técnica, parcial o completa. Registre RTO/RPO obtenidos y hallazgos.
              </p>
            </>
          )}

          {tab === "procedimientos" && (
            <>
              <h2>Procedimientos de recuperación</h2>
              <p className="muted">
                Runbooks con pasos estructurados, orden, responsable y validación. No se ejecutan comandos almacenados.
              </p>
            </>
          )}
        </section>
      )}
    </div>
  );
}
