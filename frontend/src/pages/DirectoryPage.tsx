import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiError, fetchEmployees, type EmployeeItem } from "../api";
import { EmptyState, ErrorState, LoadingState } from "../components/AsyncState";
import { EiaaxTable, type EiaaxColumn } from "../components/EiaaxTable";
import { label, LIFECYCLE_STATUS, MATURITY } from "../lib/labels";

export function DirectoryPage() {
  const navigate = useNavigate();
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

  const filtered = useMemo(() => employees.filter((e) => {
    if (statusFilter && e.lifecycle_status !== statusFilter) return false;
    if (specialtyFilter && !e.specialty.toLowerCase().includes(specialtyFilter.toLowerCase())) return false;
    return true;
  }), [employees, statusFilter, specialtyFilter]);

  const columns = useMemo<EiaaxColumn<EmployeeItem>[]>(() => [
    { key: "name", label: "Empleado", sortable: true, getValue: (e) => e.name, render: (e) => e.name },
    { key: "code", label: "Código", sortable: true, getValue: (e) => e.code, render: (e) => <span className="mono">{e.code}</span> },
    { key: "specialty", label: "Especialidad", sortable: true, getValue: (e) => e.specialty },
    {
      key: "lifecycle_status",
      label: "Estado",
      sortable: true,
      getValue: (e) => e.lifecycle_status,
      render: (e) => (
        <span className={`badge status-${e.lifecycle_status}`} title={e.lifecycle_status}>
          {label(LIFECYCLE_STATUS, e.lifecycle_status)}
        </span>
      ),
    },
    { key: "maturity", label: "Madurez", sortable: true, getValue: (e) => e.maturity, render: (e) => label(MATURITY, e.maturity) },
    {
      key: "capabilities",
      label: "Capacidades",
      getValue: (e) => e.capabilities?.join(", ") ?? "",
      render: (e) => <span className="cell-truncate" title={e.capabilities?.join(", ")}>{e.capabilities?.join(", ") || "—"}</span>,
    },
    { key: "model_name", label: "Modelo", getValue: (e) => e.model_name ?? "", render: (e) => <span className="mono">{e.model_name || "—"}</span> },
    { key: "last_certification", label: "Certificación", getValue: (e) => e.last_certification ?? "" },
    { key: "version", label: "Versión", sortable: true, getValue: (e) => e.version },
    {
      key: "actions",
      label: "",
      render: (e) => <Link to={`/empleados/${e.id}`} title="Ver detalle" onClick={(ev) => ev.stopPropagation()}>Detalle</Link>,
    },
  ], []);

  const filtersSlot = (
    <>
      <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} title="Filtrar por estado" aria-label="Filtrar por estado">
        <option value="">Todos los estados</option>
        {Object.entries(LIFECYCLE_STATUS).map(([value, text]) => (
          <option key={value} value={value}>{text}</option>
        ))}
      </select>
      <input placeholder="Filtrar especialidad" value={specialtyFilter} onChange={(e) => setSpecialtyFilter(e.target.value)} aria-label="Filtrar especialidad" />
    </>
  );

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
      </div>
      {employees.length === 0 ? (
        <EmptyState
          title="Aún no hay Empleados IA configurados"
          message="EIAAX puede proponer una arquitectura inicial tras un diagnóstico. También puede crear un empleado manualmente o explorar la demo comercial."
          action={(
            <div className="ops-actions">
              <Link className="btn primary" to="/diagnosticos">Iniciar diagnóstico</Link>
              <Link className="btn secondary" to="/demo">Ver demo comercial</Link>
              <Link className="btn secondary" to="/empleados/nuevo">Crear empleado IA</Link>
            </div>
          )}
        />
      ) : (
        <div className="panel">
          <EiaaxTable
            columns={columns}
            data={filtered}
            rowKey={(e) => e.id}
            prefsKey="directorio-empleados"
            searchPlaceholder="Buscar empleado, código o especialidad…"
            filtersSlot={filtersSlot}
            emptyMessage="Sin coincidencias para los filtros aplicados"
            onRowClick={(e) => navigate(`/empleados/${e.id}`)}
          />
        </div>
      )}
    </div>
  );
}
