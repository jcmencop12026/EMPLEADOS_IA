import { useEffect, useState } from "react";
import type { ContinuidadTablero } from "../api";
import { fetchContinuidadTablero } from "../api";
import { EVENT_HIGHLIGHT_TYPES, formatTs } from "./integrationLabels";

type TabId =
  | "tablero"
  | "servicios"
  | "planes"
  | "respaldos"
  | "incidentes"
  | "disponibilidad"
  | "pruebas"
  | "procedimientos"
  | "privacidad";

const TABS: { id: TabId; label: string }[] = [
  { id: "tablero", label: "Tablero" },
  { id: "servicios", label: "Servicios críticos" },
  { id: "respaldos", label: "Respaldos" },
  { id: "privacidad", label: "Privacidad / restore" },
  { id: "incidentes", label: "Incidentes" },
  { id: "planes", label: "Planes" },
  { id: "disponibilidad", label: "Disponibilidad" },
  { id: "pruebas", label: "Pruebas" },
  { id: "procedimientos", label: "Procedimientos" },
];

const PRIVACY_EVENT_TYPES = ["RESTORE_BLOQUEADO_PRIVACIDAD", "INTEGRACION_SALUD_RECUPERADA"];

export function ContinuidadPage() {
  const [tab, setTab] = useState<TabId>("tablero");
  const [data, setData] = useState<ContinuidadTablero | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [filtroAlerta, setFiltroAlerta] = useState("");

  useEffect(() => {
    setLoading(true);
    fetchContinuidadTablero()
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar continuidad"))
      .finally(() => setLoading(false));
  }, []);

  const alertasFiltradas =
    data?.alertas.filter((a) => {
      const q = filtroAlerta.trim().toLowerCase();
      if (!q) return true;
      return a.tipo.toLowerCase().includes(q) || a.mensaje.toLowerCase().includes(q);
    }) ?? [];

  const alertasPrivacidad = data?.alertas.filter((a) => PRIVACY_EVENT_TYPES.includes(a.tipo)) ?? [];

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Continuidad operativa</h1>
          <p className="muted">
            Salud de integraciones, respaldos, recuperaciones y bloqueos de privacidad en restore.
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
                  <dt>Incidentes abiertos</dt><dd>{data.incidentes_abiertos}</dd>
                  <dt>Backups fallidos</dt><dd>{data.backups_fallidos}</dd>
                  <dt>Restauraciones verificadas</dt><dd>{data.restauraciones_verificadas}</dd>
                  <dt>Acciones pendientes</dt><dd>{data.acciones_pendientes}</dd>
                </dl>
              </div>
              <div>
                <h2>Alertas recientes</h2>
                <input
                  placeholder="Filtrar alertas"
                  value={filtroAlerta}
                  onChange={(e) => setFiltroAlerta(e.target.value)}
                  style={{ marginBottom: "0.5rem" }}
                />
                {alertasFiltradas.length === 0 ? (
                  <p className="muted">Sin alertas activas.</p>
                ) : (
                  <table className="data-table compact">
                    <thead>
                      <tr><th>Tipo</th><th>Severidad</th><th>Mensaje</th><th>Fecha</th></tr>
                    </thead>
                    <tbody>
                      {alertasFiltradas.map((a, i) => (
                        <tr
                          key={a.id ?? `${a.tipo}-${i}`}
                          className={EVENT_HIGHLIGHT_TYPES.includes(a.tipo) ? "row-highlight" : ""}
                        >
                          <td><strong>{a.tipo}</strong></td>
                          <td>{a.severidad ?? "—"}</td>
                          <td>{a.mensaje}</td>
                          <td>{formatTs(a.created_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          )}

          {tab === "servicios" && (
            <>
              <h2>Servicios críticos</h2>
              <p className="muted">Integraciones vinculadas vía proveedor_ref connector:{'{id}'}.</p>
              <table className="data-table compact">
                <thead>
                  <tr>
                    <th>Código</th>
                    <th>Nombre</th>
                    <th>Criticidad</th>
                    <th>Estado</th>
                    <th>Proveedor ref</th>
                    <th>RTO</th>
                    <th>RPO</th>
                  </tr>
                </thead>
                <tbody>
                  {data.servicios_criticos.map((s) => (
                    <tr key={s.id} className={s.estado_operacional === "DEGRADADO" ? "row-highlight" : ""}>
                      <td>{s.codigo}</td>
                      <td>{s.nombre}</td>
                      <td>{s.criticidad}</td>
                      <td>{s.estado_operacional}</td>
                      <td className="mono-sm">{s.proveedor_ref ?? "—"}</td>
                      <td>{s.rto_valor != null ? `${s.rto_valor} ${s.rto_unidad ?? ""}` : "—"}</td>
                      <td>{s.rpo_valor != null ? `${s.rpo_valor} ${s.rpo_unidad ?? ""}` : "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}

          {tab === "respaldos" && (
            <>
              <h2>Respaldos (metadata)</h2>
              <p className="muted">
                Estados: PROGRAMADO → EJECUTADO → VERIFICADO → RESTAURADO_EN_PRUEBA. Sin secretos en metadata.
              </p>
              <table className="data-table compact">
                <thead>
                  <tr><th>Recurso</th><th>Resultado</th><th>Estado registro</th></tr>
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

          {tab === "privacidad" && (
            <>
              <h2>Privacidad y restore</h2>
              <p className="muted">
                Eventos destacados: <strong>RESTORE_BLOQUEADO_PRIVACIDAD</strong> y recuperación de integraciones.
              </p>
              {alertasPrivacidad.length === 0 ? (
                <p className="muted">Sin eventos de privacidad o recuperación registrados.</p>
              ) : (
                <table className="data-table compact">
                  <thead>
                    <tr><th>Tipo</th><th>Severidad</th><th>Mensaje</th><th>Entidad</th><th>Fecha</th></tr>
                  </thead>
                  <tbody>
                    {alertasPrivacidad.map((a, i) => (
                      <tr key={a.id ?? `p-${i}`} className="row-highlight">
                        <td><strong>{a.tipo}</strong></td>
                        <td>{a.severidad ?? "—"}</td>
                        <td>{a.mensaje}</td>
                        <td className="mono-sm">{a.entidad_ref ?? "—"}</td>
                        <td>{formatTs(a.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </>
          )}

          {tab === "incidentes" && (
            <>
              <h2>Incidentes operativos</h2>
              <p><strong>Abiertos:</strong> {data.incidentes_abiertos}</p>
              <p className="muted">Ciclo: detectado → confirmado → contención → recuperación → resuelto.</p>
            </>
          )}

          {tab === "planes" && (
            <>
              <h2>Planes de continuidad</h2>
              <p className="muted">Planes configurables con alcance, RTO/RPO y estado de revisión.</p>
            </>
          )}

          {tab === "disponibilidad" && (
            <>
              <h2>Disponibilidad y SLA/SLO</h2>
              <p><strong>Servicios degradados:</strong> {data.servicios_degradados.length}</p>
              {data.servicios_degradados.length > 0 && (
                <ul>
                  {data.servicios_degradados.map((s) => (
                    <li key={s.id}>{s.nombre} — {s.estado_operacional}</li>
                  ))}
                </ul>
              )}
            </>
          )}

          {tab === "pruebas" && (
            <>
              <h2>Pruebas de continuidad</h2>
              <p className="muted">Restauraciones simuladas y evidencia de validación.</p>
              <p>Restauraciones registradas: {data.restauraciones_verificadas}</p>
            </>
          )}

          {tab === "procedimientos" && (
            <>
              <h2>Procedimientos de recuperación</h2>
              <p className="muted">Runbooks con pasos estructurados y validación manual.</p>
            </>
          )}
        </section>
      )}
    </div>
  );
}
