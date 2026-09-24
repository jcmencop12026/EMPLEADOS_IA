import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { createEmployeeFromRequerimiento, diagnosticarTransformacion } from "../../api";
import { label, CONFIANZA } from "../../lib/evaluacionLabels";
import { EmptyState, FormSection, KpiStrip } from "../v1";

const ALT_TIPO_LABELS: Record<string, string> = {
  AUTOMATIZAR: "Automatización",
  INTEGRAR: "Integración",
  CONTRATAR: "Contratación externa",
  CAPACITAR: "Capacitación",
  REORGANIZAR: "Reorganización",
};

const ESCENARIO_LABELS: Record<string, string> = {
  CONSERVADOR: "Conservador",
  BASE: "Base",
  OPTIMISTA: "Optimista",
  PESIMISTA: "Pesimista",
};

type Props = {
  expedienteId: string;
  canGenerate?: boolean;
};

type Alt = Record<string, unknown>;
type Esc = Record<string, unknown>;
type Req = Record<string, unknown>;

function labelAltTipo(tipo: unknown): string {
  const key = String(tipo ?? "");
  return ALT_TIPO_LABELS[key] ?? key.replace(/_/g, " ").toLowerCase();
}

function labelEscenario(tipo: unknown): string {
  const key = String(tipo ?? "");
  return ESCENARIO_LABELS[key] ?? String(tipo ?? "Escenario");
}

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
    <FormSection
      title="Solución IA proyectada"
      description="Arquitectura recomendada por EIAAX: empleados IA, automatizaciones, alternativas evaluadas y escenarios de impacto."
    >
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
        <EmptyState
          title="Solución IA pendiente de generación"
          description="Ejecute la generación para obtener empleados IA especializados, automatizaciones priorizadas y escenarios comparables."
          action={
            canGenerate ? (
              <button type="button" className="btn primary" onClick={() => void load()} disabled={loading}>
                Generar solución proyectada
              </button>
            ) : undefined
          }
        />
      )}

      {data && (
        <>
          {siguiente && (
            <p className="login-notice" role="status">
              <strong>Decisión requerida:</strong> {String(siguiente.mensaje ?? siguiente.accion ?? "Revisar propuesta con el equipo")}
            </p>
          )}

          <FormSection title="Empleados IA especializados" description="Roles recomendados para cubrir el diagnóstico">
            {requerimientos.length === 0 ? (
              <EmptyState
                title="Sin empleados IA propuestos"
                description="Regenere la solución tras completar hallazgos o ajustar el diagnóstico."
              />
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
                      <td>{label(CONFIANZA, String(r.confianza ?? r.nivel_confianza ?? ""))}</td>
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
          </FormSection>

          <FormSection title="Automatizaciones e iniciativas" description="Acciones operativas priorizadas por impacto">
            {iniciativas.length === 0 && alternativas.length === 0 ? (
              <EmptyState
                title="Sin automatizaciones priorizadas"
                description="Las iniciativas aparecerán cuando el diagnóstico identifique procesos automatizables."
              />
            ) : (
              <ul className="cc-list-compact">
                {iniciativas.slice(0, 8).map((i) => (
                  <li key={String(i.id ?? i.titulo)}>
                    <strong>{String(i.titulo ?? i.nombre ?? "Iniciativa")}</strong>
                    {" — "}prioridad {String(i.prioridad ?? i.score ?? "—")}
                  </li>
                ))}
                {alternativas.filter((a) => a.tipo === "AUTOMATIZAR" || a.tipo === "INTEGRAR").slice(0, 5).map((a) => (
                  <li key={String(a.id)}>
                    {String(a.titulo ?? a.nombre)} ({labelAltTipo(a.tipo)})
                  </li>
                ))}
              </ul>
            )}
          </FormSection>

          <FormSection title="Alternativas evaluadas" description="Opciones comparadas por valor, costo y prioridad">
            {alternativas.length === 0 ? (
              <EmptyState title="Sin alternativas generadas" description="Regenere la solución para evaluar opciones." />
            ) : (
              <table className="data-table compact-table cc-table-fill">
                <thead>
                  <tr><th>Alternativa</th><th>Tipo</th><th>Valor</th><th>Costo est.</th><th>Prioridad</th></tr>
                </thead>
                <tbody>
                  {alternativas.map((a) => (
                    <tr key={String(a.id)} className={a.recomendada ? "row-highlight" : ""}>
                      <td>{String(a.titulo ?? a.nombre ?? "—")}{a.recomendada ? " ★ Recomendada" : ""}</td>
                      <td>{labelAltTipo(a.tipo)}</td>
                      <td>{String(a.valor_esperado ?? a.beneficio ?? "—")}</td>
                      <td>{String(a.costo_estimado ?? a.costo ?? "—")}</td>
                      <td>{String(a.score_total ?? "—")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </FormSection>

          <FormSection title="Escenarios de impacto" description="Comparación antes / proyectado por escenario">
            {escenarios.length === 0 ? (
              <EmptyState title="Sin escenarios proyectados" description="Los escenarios se generan con la solución IA." />
            ) : (
              <KpiStrip
                items={escenarios.map((e, idx) => ({
                  id: String(e.id ?? idx),
                  label: labelEscenario(e.tipo ?? e.nombre),
                  value: String(e.valor_neto ?? e.impacto ?? e.resumen ?? "—"),
                  hint: String(e.descripcion ?? ""),
                  tone: "value" as const,
                }))}
              />
            )}
          </FormSection>
        </>
      )}
    </FormSection>
  );
}
