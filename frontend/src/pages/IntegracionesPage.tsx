import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { IntegrationCatalogItem, IntegrationConnector } from "../api";
import { fetchIntegrationCatalog, fetchIntegrationConnectors } from "../api";

const STATUS_LABELS: Record<string, string> = {
  BORRADOR: "Borrador",
  CONFIGURANDO: "Configurando",
  VALIDANDO: "Validando",
  ACTIVO: "Activo",
  DEGRADADO: "Degradado",
  ERROR: "Error",
  INACTIVO: "Inactivo",
};

const TYPE_LABELS: Record<string, string> = {
  API_REST: "API REST",
  BASE_DATOS: "Base de datos",
  ARCHIVO: "Archivo",
  SFTP: "SFTP",
  WEBHOOK: "Webhook",
  CORREO: "Correo",
  EVENTO: "Evento",
};

export function IntegracionesPage() {
  const [connectors, setConnectors] = useState<IntegrationConnector[]>([]);
  const [catalog, setCatalog] = useState<IntegrationCatalogItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    Promise.all([fetchIntegrationConnectors(), fetchIntegrationCatalog()])
      .then(([list, cat]) => {
        setConnectors(list);
        setCatalog(cat);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar integraciones"));
  }, []);

  const filtered = connectors.filter(
    (c) =>
      !filter ||
      c.name.toLowerCase().includes(filter.toLowerCase()) ||
      c.code.toLowerCase().includes(filter.toLowerCase()),
  );

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Integraciones</h1>
          <p className="muted">
            Conectores empresariales reutilizables para alimentar señales, automatizaciones y procesos sin integraciones rígidas por cliente.
          </p>
        </div>
        <Link className="btn primary" to="/integraciones/nueva">
          Nueva integración
        </Link>
      </header>

      {error && <div className="alert alert-error">{error}</div>}

      <section className="card" style={{ marginBottom: "1.5rem" }}>
        <h2>Catálogo de tipos</h2>
        <div className="chip-row">
          {catalog.map((t) => (
            <span key={t.type} className="chip" title={t.descripcion}>
              {t.name}
            </span>
          ))}
        </div>
      </section>

      <section className="card">
        <div className="toolbar" style={{ marginBottom: "1rem" }}>
          <h2>Conectores configurados</h2>
          <input
            placeholder="Buscar por nombre o código"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
        </div>
        {filtered.length === 0 ? (
          <p className="muted">No hay conectores. Cree uno con el asistente de configuración.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Código</th>
                <th>Nombre</th>
                <th>Tipo</th>
                <th>Estado</th>
                <th>Credencial</th>
                <th>Destino</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((c) => (
                <tr key={c.id}>
                  <td>{c.code}</td>
                  <td>{c.name}</td>
                  <td>{TYPE_LABELS[c.connector_type] ?? c.connector_type}</td>
                  <td>
                    <span className={`badge status-${c.status}`}>
                      {STATUS_LABELS[c.status] ?? c.status}
                    </span>
                  </td>
                  <td>{c.secret_configured ? "Configurado" : "No configurado"}</td>
                  <td>{c.destination_type ?? "—"}</td>
                  <td>
                    <Link to={`/integraciones/${c.id}`}>Detalle</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
