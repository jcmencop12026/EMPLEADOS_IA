import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchEmployees, fetchExecutions, type EmployeeItem, type ExecutionItem } from "../../api";
import { label, EXECUTION_STATUS, LIFECYCLE_STATUS } from "../../lib/labels";

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

  return (
    <section className="panel compact-panel">
      <h2 className="section-title">Operación</h2>
      <p className="muted small scope-note">
        {isOrgScope
          ? "Recursos disponibles de la organización (no exclusivos de este expediente)."
          : "Actividad vinculada a este expediente cuando existe correlación."}
      </p>
      <div className="cc-mini-grid">
        <div>
          <h3 className="cc-subtitle">Empleados IA activos ({activos.length})</h3>
          {activos.length === 0 ? (
            <p className="muted">Sin empleados activos. <Link to="/directorio">Directorio</Link></p>
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
          <p><Link to="/directorio">Ver directorio</Link></p>
        </div>
        <div>
          <h3 className="cc-subtitle">Ejecuciones recientes ({displayExecutions.length})</h3>
          {displayExecutions.length === 0 ? (
            <p className="muted">Sin ejecuciones registradas para esta vista.</p>
          ) : (
            <ul className="cc-list-compact">
              {displayExecutions.slice(0, 6).map((x) => (
                <li key={x.plan_id}>
                  <Link to={`/ejecuciones/${x.plan_id}`}>{x.objective ?? `Plan ${x.plan_id.slice(0, 8)}`}</Link>
                  {" · "}
                  <span className="estado-badge">{label(EXECUTION_STATUS, x.status)}</span>
                </li>
              ))}
            </ul>
          )}
          <p><Link to="/ejecuciones">Todas las ejecuciones</Link> · <Link to="/automatizaciones">Automatizaciones</Link></p>
        </div>
      </div>
      <p className="muted small">
        <Link to="/aprobaciones">Aprobaciones</Link>
        {" · "}
        <Link to="/trabajo">Mi trabajo</Link>
      </p>
    </section>
  );
}
