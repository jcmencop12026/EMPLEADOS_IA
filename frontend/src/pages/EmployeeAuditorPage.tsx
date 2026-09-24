import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  ApiError,
  executeEmployeeAudit,
  fetchEmployeeAuditFindings,
  fetchEmployeeAuditHealth,
  type EmployeeAuditFinding,
  type EmployeeAuditHealthRow,
} from "../api";
import { EmptyState, ErrorState, LoadingState } from "../components/AsyncState";
import { usePermissions } from "../hooks/usePermissions";

const HEALTH_LABELS: Record<string, string> = {
  SALUDABLE: "Saludable",
  OBSERVAR: "Observar",
  REQUIERE_MEJORA: "Requiere mejora",
  REQUIERE_INTERVENCION: "Requiere intervención",
  CRITICO: "Crítico",
};

const HEALTH_CLASS: Record<string, string> = {
  SALUDABLE: "badge ok",
  OBSERVAR: "badge warn",
  REQUIERE_MEJORA: "badge warn",
  REQUIERE_INTERVENCION: "badge danger",
  CRITICO: "badge danger",
};

function formatTs(value?: string | null) {
  if (!value) return "—";
  return new Date(value).toLocaleString("es");
}

export function EmployeeAuditorPage() {
  const { has } = usePermissions();
  const canExecute = has("auditor_empleados.execute");
  const [searchParams] = useSearchParams();
  const filterEmployeeId = searchParams.get("employee_id") ?? "";

  const [healthRows, setHealthRows] = useState<EmployeeAuditHealthRow[]>([]);
  const [findings, setFindings] = useState<EmployeeAuditFinding[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [acting, setActing] = useState<string | null>(null);
  const [selected, setSelected] = useState<EmployeeAuditHealthRow | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    const findingsParams: Record<string, string> = { status: "ABIERTO" };
    if (filterEmployeeId) findingsParams.employee_id = filterEmployeeId;
    Promise.all([fetchEmployeeAuditHealth(), fetchEmployeeAuditFindings(findingsParams)])
      .then(([health, hallazgos]) => {
        setHealthRows(health);
        setFindings(hallazgos);
        if (filterEmployeeId) {
          const row = health.find((h) => h.employee_id === filterEmployeeId);
          setSelected(row ?? null);
        }
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Error al cargar auditoría de empleados."))
      .finally(() => setLoading(false));
  }, [filterEmployeeId]);

  useEffect(() => {
    load();
  }, [load]);

  const filteredHealth = useMemo(() => {
    if (!filterEmployeeId) return healthRows;
    return healthRows.filter((r) => r.employee_id === filterEmployeeId);
  }, [healthRows, filterEmployeeId]);

  const selectedFindings = useMemo(() => {
    if (!selected) return findings;
    return findings.filter((f) => f.employee_id === selected.employee_id);
  }, [findings, selected]);

  async function runAudit(employeeId?: string) {
    setActing(employeeId ?? "all");
    try {
      await executeEmployeeAudit({
        employee_id: employeeId,
        scope: employeeId ? "ALL" : "ACTIVE",
      });
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo ejecutar la auditoría.");
    } finally {
      setActing(null);
    }
  }

  if (loading) return <LoadingState message="Cargando auditoría de empleados…" />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  return (
    <div className="ops-page">
      <header className="page-header">
        <div>
          <h1>Auditoría de Empleados IA</h1>
          <p className="muted">Salud determinística, hallazgos y recomendaciones (sin LLM)</p>
        </div>
        {canExecute && (
          <div className="header-actions">
            <button
              type="button"
              className="btn primary"
              disabled={acting !== null}
              onClick={() => runAudit()}
            >
              {acting === "all" ? "Auditando…" : "Auditar empleados activos"}
            </button>
          </div>
        )}
      </header>

      <div className="panel table-wrap">
        <h2>Salud por empleado</h2>
        {filteredHealth.length === 0 ? (
          <EmptyState title="Sin empleados" message="No hay empleados activos para auditar." />
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Empleado</th>
                <th>Salud</th>
                <th>Última auditoría</th>
                <th>Hallazgos abiertos</th>
                <th>Críticos</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {filteredHealth.map((row) => (
                <tr
                  key={row.employee_id}
                  className={selected?.employee_id === row.employee_id ? "row-selected" : ""}
                  onClick={() => setSelected(row)}
                >
                  <td>
                    <Link to={`/empleados/${row.employee_id}`}>{row.employee_name}</Link>
                  </td>
                  <td>
                    <span className={HEALTH_CLASS[row.health_status] ?? "badge"}>
                      {HEALTH_LABELS[row.health_status] ?? row.health_status}
                    </span>
                  </td>
                  <td>{formatTs(row.last_audit_at)}</td>
                  <td>{row.open_findings}</td>
                  <td>{row.critical_findings}</td>
                  <td>
                    <button
                      type="button"
                      className="btn link"
                      disabled={!canExecute || acting !== null}
                      onClick={(e) => {
                        e.stopPropagation();
                        runAudit(row.employee_id);
                      }}
                    >
                      {acting === row.employee_id ? "…" : "Auditar"}
                    </button>
                    <button type="button" className="btn link" onClick={() => setSelected(row)}>
                      Detalle
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="panel table-wrap">
        <h2>
          Hallazgos
          {selected ? ` — ${selected.employee_name}` : ""}
        </h2>
        {selectedFindings.length === 0 ? (
          <EmptyState title="Sin hallazgos" message="No hay hallazgos abiertos en el alcance seleccionado." />
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Severidad</th>
                <th>Título</th>
                <th>Regla</th>
                <th>Acción recomendada</th>
                <th>Estado</th>
                <th>Fecha</th>
              </tr>
            </thead>
            <tbody>
              {selectedFindings.map((f) => (
                <tr key={f.id}>
                  <td>
                    <span className={f.severity === "CRITICO" ? "badge danger" : "badge warn"}>
                      {f.severity}
                    </span>
                  </td>
                  <td title={f.detail ?? ""}>{f.title}</td>
                  <td className="mono">{f.rule_code}</td>
                  <td>{f.recommended_action ?? "—"}</td>
                  <td>{f.status}</td>
                  <td>{formatTs(f.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
