import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { createEmployeeFromRequerimiento, diagnosticarTransformacion } from "../../api";

type Props = {
  expedienteId: string;
  canGenerate?: boolean;
};

type Alt = Record<string, unknown>;
type Esc = Record<string, unknown>;
type Req = Record<string, unknown>;

export function SolucionIaProyectadaPanel({ expedienteId, canGenerate = true }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<Record<string, unknown> | null>(null);

  const load = useCallback(async () => {
    if (!canGenerate) return;
    setLoading(true);
    setError(null);
    try {
      const result = await diagnosticarTransformacion(expedienteId);
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo generar la solución proyectada");
    } finally {
      setLoading(false);
    }
  }, [expedienteId, canGenerate]);

  useEffect(() => {
    if (canGenerate) {
      void load();
    }
  }, [load, canGenerate]);

  const alternativas = (data?.alternativas as Alt[]) ?? [];
  const escenarios = (data?.escenarios as Esc[]) ?? [];
  const requerimientos = (data?.empleado_ia_requerimientos as Req[]) ?? [];
  const iniciativas = (data?.iniciativas as Record<string, unknown>[]) ?? [];
  const siguiente = data?.siguiente_accion as Record<string, unknown> | undefined;

  async function onCrearEmpleado(reqId: string) {
    try {
      const r = await createEmployeeFromRequerimiento(reqId);
      const empId = (r.employee as { id?: string })?.id;
      if (empId) window.location.href = `/empleados/${empId}`;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al crear empleado IA");
    }
  }

  return (
    <section className="panel compact-panel solucion-ia-panel">
      <header className="cc-zone-head">
        <h2 className="section-title">Solución IA proyectada</h2>
        <p className="muted small">
          Arquitectura inicial recomendada por EIAAX a partir del diagnóstico del expediente.
        </p>
      </header>

      {canGenerate && (
        <div className="ops-actions">
          <button type="button" className="btn secondary" onClick={() => void load()} disabled={loading}>
            {loading ? "Generando…" : "Regenerar solución"}
          </button>
          <Link className="btn secondary" to="/arquitecto-transformacion">Arquitecto de transformación</Link>
        </div>
      )}

      {error && <p className="error">{error}</p>}
      {loading && !data && <p className="muted">Analizando expediente y proyectando arquitectura…</p>}

      {!loading && !data && !error && (
        <p className="muted">Ejecute la generación para obtener empleados IA, automatizaciones y escenarios propuestos.</p>
      )}

      {data && (
        <>
          {siguiente && (
            <p className="login-notice" role="status">
              <strong>Siguiente paso:</strong> {String(siguiente.mensaje ?? siguiente.accion ?? "Revisar propuesta")}
            </p>
          )}

          <div className="cc-cockpit-grid">
            <div>
              <h3 className="cc-subtitle">Empleados IA especializados</h3>
              {requerimientos.length === 0 ? (
                <p className="muted">Sin requerimientos de empleados IA en esta proyección.</p>
              ) : (
                <table className="data-table compact-table cc-table-fill">
                  <thead>
                    <tr><th>Función</th><th>Objetivo</th><th>Confianza</th><th></th></tr>
                  </thead>
                  <tbody>
                    {requerimientos.map((r) => (
                      <tr key={String(r.id)}>
                        <td>{String(r.titulo ?? r.nombre ?? "—")}</td>
                        <td>{String(r.objetivo ?? r.descripcion ?? "—")}</td>
                        <td>{String(r.confianza ?? r.nivel_confianza ?? "—")}</td>
                        <td>
                          {r.id && (
                            <button type="button" className="btn small" onClick={() => void onCrearEmpleado(String(r.id))}>
                              Crear empleado
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            <div>
              <h3 className="cc-subtitle">Automatizaciones e iniciativas</h3>
              {iniciativas.length === 0 && alternativas.length === 0 ? (
                <p className="muted">Sin automatizaciones priorizadas.</p>
              ) : (
                <ul className="cc-list-compact">
                  {iniciativas.slice(0, 8).map((i) => (
                    <li key={String(i.id ?? i.titulo)}>
                      {String(i.titulo ?? i.nombre ?? "Iniciativa")} — prioridad {String(i.prioridad ?? i.score ?? "—")}
                    </li>
                  ))}
                  {alternativas.filter((a) => a.tipo === "AUTOMATIZAR" || a.tipo === "INTEGRAR").slice(0, 5).map((a) => (
                    <li key={String(a.id)}>
                      {String(a.titulo ?? a.nombre)} ({String(a.tipo)})
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          <h3 className="cc-subtitle">Alternativas evaluadas</h3>
          {alternativas.length === 0 ? (
            <p className="muted">Sin alternativas generadas.</p>
          ) : (
            <table className="data-table compact-table cc-table-fill">
              <thead>
                <tr><th>Alternativa</th><th>Tipo</th><th>Valor</th><th>Costo est.</th><th>Score</th></tr>
              </thead>
              <tbody>
                {alternativas.map((a) => (
                  <tr key={String(a.id)} className={a.recomendada ? "row-highlight" : ""}>
                    <td>{String(a.titulo ?? a.nombre ?? "—")}{a.recomendada ? " ★" : ""}</td>
                    <td>{String(a.tipo ?? "—")}</td>
                    <td>{String(a.valor_esperado ?? a.beneficio ?? "—")}</td>
                    <td>{String(a.costo_estimado ?? a.costo ?? "—")}</td>
                    <td>{String(a.score_total ?? "—")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <h3 className="cc-subtitle">Escenarios (antes / proyectado)</h3>
          {escenarios.length === 0 ? (
            <p className="muted">Sin escenarios proyectados.</p>
          ) : (
            <div className="cc-kpi-strip">
              {escenarios.map((e) => (
                <div key={String(e.id ?? e.tipo)} className="cc-kpi-item">
                  <span className="cc-kpi-label">{String(e.tipo ?? e.nombre ?? "Escenario")}</span>
                  <strong className="cc-kpi-value">{String(e.valor_neto ?? e.impacto ?? e.resumen ?? "—")}</strong>
                  <span className="muted small">{String(e.descripcion ?? "")}</span>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </section>
  );
}
