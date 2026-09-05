import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchEmployees, fetchExecutions, type EmployeeItem, type ExecutionItem } from "../../api";
import { label, EXECUTION_STATUS, LIFECYCLE_STATUS } from "../../lib/labels";
import { EmptyState, FormSection, KpiStrip } from "../v1";

type Props = {
  expedienteId?: string;
};

export function EmpresaOperacionPanel({ expedienteId }: Props) {
  const [employees, setEmployees] = useState<EmployeeItem[]>([]);
  const [executions, setExecutions] = useState<ExecutionItem[]>([]);

  useEffect(() => {
    fetchEmployees().then(setEmployees).catch(() => undefined);
    fetchExecutions().then(setExecutions).catch(() => undefined);
  }, [expedienteId]);

  const activos = employees.filter((e) => e.lifecycle_status === "ACTIVE" || e.lifecycle_status === "PUBLISHED");
  const scopedExecutions = expedienteId
    ? executions.filter((x) => x.correlation_id === expedienteId || String(x.objective ?? "").includes(expedienteId.slice(0, 8)))
    : executions;
  const displayExecutions = scopedExecutions.length > 0 ? scopedExecutions : executions.slice(0, 6);
  const isOrgScope = scopedExecutions.length === 0 && executions.length > 0;
  const pendingApprovalsHint = displayExecutions.filter((x) => x.status === "WAITING_APPROVAL").length;

  return (
    <FormSection
      title="Operación"
      description={
        isOrgScope
          ? "Recursos disponibles de la organización. La actividad exclusiva del expediente aparece cuando existe correlación."
          : "Empleados IA, automatizaciones y ejecuciones vinculadas a este expediente."
      }
    >
      <KpiStrip
        items={[
          { id: "emp", label: "Empleados IA activos", value: activos.length, href: "/directorio" },
          { id: "exec", label: "Ejecuciones recientes", value: displayExecutions.length, href: "/ejecuciones" },
          {
            id: "appr",
            label: "Pendientes aprobación",
            value: pendingApprovalsHint,
            tone: pendingApprovalsHint > 0 ? "attention" : "default",
            href: "/aprobaciones",
          },
        ]}
      />

      <div className="cc-mini-grid">
        <div>
          <h3 className="cc-subtitle">Empleados IA activos</h3>
          {activos.length === 0 ? (
            <EmptyState
              title="Sin empleados activos"
              description="Cree empleados IA desde la solución proyectada o el directorio para operar automatizaciones."
              action={<Link to="/directorio" className="btn primary small">Ir al directorio</Link>}
            />
          ) : (
            <ul className="cc-list-compact">
              {activos.slice(0, 6).map((e) => (
                <li key={e.id}>
                  <Link to={`/empleados/${e.id}`}>{e.name}</Link> · {e.specialty}
                  <span className="muted small"> · {label(LIFECYCLE_STATUS, e.lifecycle_status)}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div>
          <h3 className="cc-subtitle">Ejecuciones recientes</h3>
          {displayExecutions.length === 0 ? (
            <EmptyState
              title="Sin ejecuciones registradas"
              description="Las ejecuciones aparecen cuando se activan planes de trabajo o automatizaciones vinculadas al expediente."
              action={
                <div className="ops-actions">
                  <Link to="/automatizaciones" className="btn primary small">Automatizaciones</Link>
                  <Link to="/ejecuciones" className="btn secondary small">Ver ejecuciones</Link>
                </div>
              }
            />
          ) : (
            <ul className="cc-list-compact">
              {displayExecutions.slice(0, 6).map((x) => (
                <li key={x.plan_id}>
                  <Link to={`/ejecuciones/${x.plan_id}`}>
                    {x.objective ?? "Plan de trabajo"}
                  </Link>
                  {" · "}
                  <span className="estado-badge">{label(EXECUTION_STATUS, x.status)}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div className="ops-actions">
        <Link to="/aprobaciones" className="btn secondary small">Aprobaciones</Link>
        <Link to="/trabajo" className="btn secondary small">Mi trabajo</Link>
        <Link to="/automatizaciones" className="btn secondary small">Automatizaciones</Link>
      </div>
    </FormSection>
  );
}
