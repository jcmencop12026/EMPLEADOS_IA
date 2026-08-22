import { useEffect, useState } from "react";
import type { EmployeeItem } from "../api";
import { fetchEmployees } from "../api";

const STATUS_LABEL: Record<string, string> = {
  DISPONIBLE: "Disponible",
  PLANIFICANDO: "Planificando",
  TRABAJANDO: "Trabajando",
  ESPERANDO_APROBACION: "Esperando aprobación",
  ERROR: "Error",
};

export function DirectoryPage() {
  const [employees, setEmployees] = useState<EmployeeItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchEmployees()
      .then(setEmployees)
      .catch((e) => setError(e instanceof Error ? e.message : "Error"));
  }, []);

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Directorio Operacional</h1>
        <p className="muted">Empleados IA · Workspace Salud</p>
      </header>
      {error && <p className="error">{error}</p>}
      <div className="panel table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Empleado</th>
              <th>Especialidad</th>
              <th>Estado</th>
              <th>Proveedor</th>
              <th>Modelo</th>
            </tr>
          </thead>
          <tbody>
            {employees.map((e) => (
              <tr key={e.id}>
                <td>{e.name}</td>
                <td>{e.specialty}</td>
                <td>
                  <span className={`badge emp-${e.status}`}>
                    {STATUS_LABEL[e.status] || e.status}
                  </span>
                </td>
                <td>{e.model_provider || "—"}</td>
                <td className="mono">{e.model_name || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
