import { useCallback, useEffect, useState } from "react";
import type {
  GovCatalogEntry,
  GovClassification,
  GovDashboard,
  GovDataCategory,
  GovFinding,
  GovRetentionPolicy,
  GovSubjectRequest,
} from "../api";
import {
  createGovCatalogEntry,
  fetchGovAccessLogs,
  fetchGovCatalog,
  fetchGovCategories,
  fetchGovClassifications,
  fetchGovDashboard,
  fetchGovFindings,
  fetchGovRetentionPolicies,
  fetchGovSubjectRequests,
  scanGovFindings,
} from "../api";
import { SemanticBadge } from "../components/SemanticBadge";

type Tab = "tablero" | "catalogo" | "clasificacion" | "politicas" | "retencion" | "accesos" | "solicitudes" | "hallazgos";

const TABS: { id: Tab; label: string }[] = [
  { id: "tablero", label: "Tablero" },
  { id: "catalogo", label: "Catálogo" },
  { id: "clasificacion", label: "Clasificación" },
  { id: "politicas", label: "Políticas" },
  { id: "retencion", label: "Retención" },
  { id: "accesos", label: "Accesos" },
  { id: "solicitudes", label: "Solicitudes" },
  { id: "hallazgos", label: "Hallazgos" },
];

export function GobernanzaDatosPage() {
  const [tab, setTab] = useState<Tab>("tablero");
  const [error, setError] = useState<string | null>(null);
  const [dashboard, setDashboard] = useState<GovDashboard | null>(null);
  const [catalog, setCatalog] = useState<GovCatalogEntry[]>([]);
  const [classifications, setClassifications] = useState<GovClassification[]>([]);
  const [categories, setCategories] = useState<GovDataCategory[]>([]);
  const [retention, setRetention] = useState<GovRetentionPolicy[]>([]);
  const [accesses, setAccesses] = useState<Array<Record<string, unknown>>>([]);
  const [requests, setRequests] = useState<GovSubjectRequest[]>([]);
  const [findings, setFindings] = useState<GovFinding[]>([]);

  const load = useCallback(() => {
    setError(null);
    const tasks: Promise<void>[] = [
      fetchGovDashboard().then(setDashboard).catch((e) => setError(String(e))),
      fetchGovCatalog().then(setCatalog).catch(() => undefined),
      fetchGovClassifications().then(setClassifications).catch(() => undefined),
      fetchGovCategories().then(setCategories).catch(() => undefined),
      fetchGovRetentionPolicies().then(setRetention).catch(() => undefined),
      fetchGovAccessLogs().then(setAccesses).catch(() => undefined),
      fetchGovSubjectRequests().then(setRequests).catch(() => undefined),
      fetchGovFindings().then(setFindings).catch(() => undefined),
    ];
    return Promise.all(tasks);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleCreateCatalog(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    await createGovCatalogEntry({
      name: String(form.get("name") || "Fuente"),
      description: String(form.get("description") || ""),
      data_environment: String(form.get("data_environment") || "PRODUCCION"),
      functional_owner: String(form.get("functional_owner") || "") || undefined,
    });
    await load();
  }

  async function handleScanFindings() {
    await scanGovFindings();
    await load();
  }

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Gobierno de datos</h1>
        <p className="muted">Catálogo, clasificación, políticas, retención, accesos y privacidad</p>
      </header>
      {error && <p className="error">{error}</p>}

      <div className="tab-bar">
        {TABS.map((t) => (
          <button key={t.id} type="button" className={tab === t.id ? "tab active" : "tab"} onClick={() => setTab(t.id)}>
            {t.label}
          </button>
        ))}
      </div>

      {tab === "tablero" && dashboard && (
        <section className="card-grid">
          <div className="card"><h3>Fuentes catalogadas</h3><p className="metric">{dashboard.fuentes_catalogadas}</p></div>
          <div className="card"><h3>Sin clasificar</h3><p className="metric">{dashboard.sin_clasificar}</p></div>
          <div className="card"><h3>Riesgo alto</h3><p className="metric">{dashboard.riesgo_alto}</p><SemanticBadge tipo={dashboard.riesgo_alto_semantico?.tipo_semantico ?? "INFERENCIA"} tooltip={dashboard.riesgo_alto_semantico?.tooltip_semantico} /></div>
          <div className="card"><h3>Retención vencida</h3><p className="metric">{dashboard.retencion_vencida}</p></div>
          <div className="card"><h3>Exportaciones</h3><p className="metric">{dashboard.exportaciones}</p></div>
          <div className="card"><h3>Solicitudes abiertas</h3><p className="metric">{dashboard.solicitudes_abiertas}</p></div>
          <div className="card"><h3>Hallazgos</h3><p className="metric">{dashboard.hallazgos_abiertos}</p></div>
          <div className="card"><h3>Acciones pendientes</h3><p className="metric">{dashboard.acciones_pendientes}</p></div>
        </section>
      )}

      {tab === "catalogo" && (
        <section>
          <form className="inline-form" onSubmit={handleCreateCatalog}>
            <input name="name" placeholder="Nombre de fuente" required />
            <input name="functional_owner" placeholder="Propietario funcional" />
            <select name="data_environment">
              <option value="PRODUCCION">Producción</option>
              <option value="PRUEBA">Prueba</option>
              <option value="SINTETICO">Sintético</option>
            </select>
            <button type="submit">Registrar fuente</button>
          </form>
          <table className="data-table">
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Clasificación</th>
                <th>Ambiente</th>
                <th>Estado</th>
                <th>Propietario</th>
              </tr>
            </thead>
            <tbody>
              {catalog.map((row) => (
                <tr key={row.id}>
                  <td>{row.name}</td>
                  <td>{row.classification_name ?? "—"}</td>
                  <td>{row.data_environment}</td>
                  <td>{row.status}</td>
                  <td>{row.functional_owner ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {tab === "clasificacion" && (
        <section className="two-col">
          <div>
            <h2>Niveles de clasificación</h2>
            <ul>
              {classifications.map((c) => (
                <li key={c.id}>{c.name} ({c.code}) — rango {c.sensitivity_rank}</li>
              ))}
            </ul>
          </div>
          <div>
            <h2>Categorías de información</h2>
            <ul>
              {categories.map((c) => (
                <li key={c.id}>{c.name} ({c.code})</li>
              ))}
            </ul>
          </div>
        </section>
      )}

      {tab === "politicas" && (
        <section>
          <p className="muted">Políticas de salida a proveedores IA y minimización configurables por organización y clasificación.</p>
          <p>Consulte y gestione políticas desde la API <code>/api/gobierno-datos/politicas-proveedor</code>.</p>
        </section>
      )}

      {tab === "retencion" && (
        <section>
          <table className="data-table">
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Alcance</th>
                <th>Duración</th>
                <th>Disposición</th>
              </tr>
            </thead>
            <tbody>
              {retention.map((r) => (
                <tr key={r.id}>
                  <td>{r.name}</td>
                  <td>{r.scope_type}</td>
                  <td>{r.duration_value ?? "—"} {r.duration_unit}</td>
                  <td>{r.disposition}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {tab === "accesos" && (
        <section>
          <table className="data-table">
            <thead>
              <tr>
                <th>Acción</th>
                <th>Resultado</th>
                <th>Recurso</th>
                <th>Fecha</th>
              </tr>
            </thead>
            <tbody>
              {accesses.map((a) => (
                <tr key={String(a.id)}>
                  <td>{String(a.action)}</td>
                  <td>{String(a.result)}</td>
                  <td>{String(a.resource_ref ?? a.catalog_entry_id ?? "—")}</td>
                  <td>{String(a.created_at ?? "")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {tab === "solicitudes" && (
        <section>
          <table className="data-table">
            <thead>
              <tr>
                <th>Tipo</th>
                <th>Estado</th>
                <th>Referencia</th>
                <th>Creada</th>
              </tr>
            </thead>
            <tbody>
              {requests.map((r) => (
                <tr key={r.id}>
                  <td>{r.request_type}</td>
                  <td>{r.status}</td>
                  <td>{r.subject_ref ?? "—"}</td>
                  <td>{r.created_at ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {tab === "hallazgos" && (
        <section>
          <button type="button" onClick={handleScanFindings}>Escanear hallazgos</button>
          <table className="data-table">
            <thead>
              <tr>
                <th>Semántica</th>
                <th>Tipo</th>
                <th>Severidad</th>
                <th>Descripción</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {findings.map((f) => (
                <tr key={f.id}>
                  <td><SemanticBadge tipo={f.tipo_semantico ?? "INFERENCIA"} subtipo={f.subtipo_semantico} tooltip={f.tooltip_semantico} /></td>
                  <td>{f.finding_type}</td>
                  <td>{f.severity}</td>
                  <td>{f.description}</td>
                  <td>{f.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}
