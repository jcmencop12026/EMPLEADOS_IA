import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchEmployees, fetchExecutions, type EmployeeItem, type ExecutionItem } from "../../api";

export function EmpresaOperacionPanel() {
  const [employees, setEmployees] = useState<EmployeeItem[]>([]);
  const [executions, setExecutions] = useState<ExecutionItem[]>([]);

  useEffect(() => {
    fetchEmployees().then(setEmployees).catch(() => undefined);
    fetchExecutions().then(setExecutions).catch(() => undefined);
  }, []);

  const activos = employees.filter((e) => e.lifecycle_status === "ACTIVE" || e.lifecycle_status === "PRODUCTION");

  return (
    <section className="panel compact-panel">
      <h2 className="section-title">Operación</h2>
      <div className="cc-mini-grid">
        <div>
          <h3 className="cc-subtitle">Empleados IA ({activos.length})</h3>
          {activos.length === 0 ? (
            <p className="muted">Sin empleados activos. <Link to="/directorio">Directorio</Link></p>
          ) : (
            <ul className="cc-list-compact">
              {activos.slice(0, 6).map((e) => (
                <li key={e.id}><Link to={`/empleados/${e.id}`}>{e.name}</Link> · {e.specialty}</li>
              ))}
            </ul>
          )}
          <p><Link to="/directorio">Ver directorio</Link> · <Link to="/empleados/nuevo">Crear empleado</Link></p>
        </div>
        <div>
          <h3 className="cc-subtitle">Ejecuciones recientes ({executions.length})</h3>
          {executions.length === 0 ? (
            <p className="muted">Sin ejecuciones registradas.</p>
          ) : (
            <ul className="cc-list-compact">
              {executions.slice(0, 6).map((x) => (
                <li key={x.plan_id}>
                  <Link to={`/ejecuciones/${x.plan_id}`}>{x.objective ?? x.plan_id.slice(0, 8)}</Link> · {x.status}
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
