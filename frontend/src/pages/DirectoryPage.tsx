import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ApiError, fetchEmployees, type EmployeeItem } from "../api";
import { EmptyState, ErrorState, LoadingState } from "../components/AsyncState";
import { label, LIFECYCLE_STATUS, MATURITY } from "../lib/labels";

export function DirectoryPage() {
  const [employees, setEmployees] = useState<EmployeeItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [specialtyFilter, setSpecialtyFilter] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchEmployees()
      .then(setEmployees)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Error al cargar el directorio."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const filtered = employees.filter((e) => {
    if (statusFilter && e.lifecycle_status !== statusFilter) return false;
    if (specialtyFilter && !e.specialty.toLowerCase().includes(specialtyFilter.toLowerCase())) return false;
    return true;
  });

  if (loading) return <LoadingState message="Cargando directorio…" />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Directorio de Empleados IA</h1>
        <p className="muted">Empleados especializados activos, en diseño y bajo gobierno de la plataforma EIAAX</p>
      </header>
      <div className="ops-actions">
        <Link className="btn primary" to="/empleados/nuevo" title="Crear empleado">
          + Crear empleado
        </Link>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} title="Filtrar por estado" aria-label="Filtrar por estado">
          <option value="">Todos los estados</option>
          {Object.entries(LIFECYCLE_STATUS).map(([value, text]) => (
            <option key={value} value={value}>{text}</option>
          ))}
        </select>
        <input placeholder="Filtrar especialidad" value={specialtyFilter} onChange={(e) => setSpecialtyFilter(e.target.value)} aria-label="Filtrar especialidad" />
      </div>
      {filtered.length === 0 ? (
        <EmptyState
          title={employees.length === 0 ? "Aún no hay Empleados IA configurados" : "Sin coincidencias"}
          message={
            employees.length === 0
              ? "EIAAX puede proponer una arquitectura inicial tras un diagnóstico. También puede crear un empleado manualmente o explorar la demo comercial."
              : "Ajuste los filtros o limpie la búsqueda para ver más resultados."
          }
          action={
            employees.length === 0 ? (
              <div className="ops-actions">
                <Link className="btn primary" to="/diagnosticos">Iniciar diagnóstico</Link>
                <Link className="btn secondary" to="/demo">Ver demo comercial</Link>
                <Link className="btn secondary" to="/empleados/nuevo">Crear empleado IA</Link>
              </div>
            ) : undefined
          }
        />
      ) : (
        <div className="panel table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Empleado</th>
                <th>Código</th>
                <th>Especialidad</th>
                <th>Estado</th>
                <th>Madurez</th>
                <th>Capacidades</th>
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
                  <td>
                    <span className={`badge status-${e.lifecycle_status}`} title={e.lifecycle_status}>
                      {label(LIFECYCLE_STATUS, e.lifecycle_status)}
                    </span>
                  </td>
                  <td>{label(MATURITY, e.maturity)}</td>
                  <td className="cell-truncate" title={e.capabilities?.join(", ")}>{e.capabilities?.join(", ") || "—"}</td>
                  <td className="mono">{e.model_name || "—"}</td>
                  <td>{e.last_certification || "—"}</td>
                  <td>{e.version}</td>
                  <td><Link to={`/empleados/${e.id}`} title="Ver detalle">Detalle</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
