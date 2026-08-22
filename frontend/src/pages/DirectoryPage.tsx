import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { EmployeeItem } from "../api";
import { fetchEmployees } from "../api";

export function DirectoryPage() {
  const [employees, setEmployees] = useState<EmployeeItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [specialtyFilter, setSpecialtyFilter] = useState("");

  useEffect(() => {
    fetchEmployees()
      .then(setEmployees)
      .catch((e) => setError(e instanceof Error ? e.message : "Error"));
  }, []);

  const filtered = employees.filter((e) => {
    if (statusFilter && e.lifecycle_status !== statusFilter) return false;
    if (specialtyFilter && !e.specialty.toLowerCase().includes(specialtyFilter.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Directorio Operacional</h1>
        <p className="muted">Empleados IA · Agent Factory</p>
      </header>
      <div className="ops-actions">
        <Link className="btn primary" to="/empleados/nuevo">+ Crear empleado</Link>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} title="Filtrar por estado">
          <option value="">Todos los estados</option>
          <option value="ACTIVE">ACTIVE</option>
          <option value="DRAFT">DRAFT</option>
          <option value="CERTIFIED">CERTIFIED</option>
          <option value="PUBLISHED">PUBLISHED</option>
        </select>
        <input placeholder="Filtrar especialidad" value={specialtyFilter} onChange={(e) => setSpecialtyFilter(e.target.value)} />
      </div>
      {error && <p className="error">{error}</p>}
      <div className="panel table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Empleado</th>
              <th>Código</th>
              <th>Especialidad</th>
              <th>Estado</th>
              <th>Madurez</th>
              <th>Capabilities</th>
              <th>Modelo</th>
              <th>Certificación</th>
              <th>Versión</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((e) => (
              <tr key={e.id}>
                <td>{e.name}</td>
                <td className="mono">{e.code}</td>
                <td>{e.specialty}</td>
                <td><span className={`badge status-${e.lifecycle_status}`}>{e.lifecycle_status}</span></td>
                <td>{e.maturity}</td>
                <td className="cell-truncate" title={e.capabilities?.join(", ")}>{e.capabilities?.join(", ") || "—"}</td>
                <td className="mono">{e.model_name || "—"}</td>
                <td>{e.last_certification || "—"}</td>
                <td>{e.version}</td>
                <td><Link to={`/empleados/${e.id}`}>Detalle</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
