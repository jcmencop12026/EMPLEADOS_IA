import { useEffect, useState } from "react";
import type { CatalogItem } from "../api";
import {
  createKnowledgeSource,
  fetchKnowledgeCatalog,
  ingestKnowledge,
  setKnowledgeStatus,
} from "../api";

export function KnowledgePage() {
  const [items, setItems] = useState<CatalogItem[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [ingestId, setIngestId] = useState<string | null>(null);
  const [ingestText, setIngestText] = useState("");
  const [form, setForm] = useState({ name: "", code: "", source_type: "TEXT", description: "" });

  async function load() {
    setLoading(true);
    setError(null);
    try {
      setItems(await fetchKnowledgeCatalog(search || undefined));
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudieron cargar las fuentes");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await createKnowledgeSource(form);
      setShowForm(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al crear");
    }
  }

  async function handleIngest(e: React.FormEvent) {
    e.preventDefault();
    if (!ingestId) return;
    setError(null);
    try {
      await ingestKnowledge(ingestId, ingestText, "text/plain");
      setIngestId(null);
      setIngestText("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error en ingesta");
    }
  }

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Fuentes de conocimiento</h1>
        <p className="muted">Definición de fuentes consultables por Empleados IA</p>
      </header>
      <div className="ops-actions">
        <input placeholder="Buscar…" value={search} onChange={(e) => setSearch(e.target.value)} onKeyDown={(e) => e.key === "Enter" && load()} />
        <button type="button" className="btn" onClick={load}>Buscar</button>
        <button type="button" className="btn primary" onClick={() => setShowForm((v) => !v)}>+ Nueva</button>
      </div>
      {showForm && (
        <form className="panel form-grid" onSubmit={handleCreate}>
          <input required placeholder="Nombre" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <input placeholder="Código (opcional)" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} />
          <select value={form.source_type} onChange={(e) => setForm({ ...form, source_type: e.target.value })}>
            <option value="TEXT">Texto / Nota</option>
            <option value="FILE">Archivo</option>
            <option value="URL">URL / Web</option>
            <option value="DATABASE">Base de datos</option>
            <option value="API">API</option>
          </select>
          <textarea placeholder="Descripción" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          <button type="submit" className="btn primary">Guardar</button>
        </form>
      )}
      {ingestId && (
        <form className="panel form-grid" onSubmit={handleIngest}>
          <h3>Ingesta de texto</h3>
          <textarea required rows={5} value={ingestText} onChange={(e) => setIngestText(e.target.value)} placeholder="Contenido…" />
          <div className="ops-actions">
            <button type="submit" className="btn primary">Procesar</button>
            <button type="button" className="btn" onClick={() => setIngestId(null)}>Cancelar</button>
          </div>
        </form>
      )}
      {loading && <p className="muted">Cargando…</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && items.length === 0 && <p className="muted">Sin fuentes registradas.</p>}
      {!loading && items.length > 0 && (
        <div className="panel table-wrap">
          <table className="data-table">
            <thead>
              <tr><th>Código</th><th>Nombre</th><th>Tipo</th><th>Estado</th><th>Acciones</th></tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td className="mono">{item.code}</td>
                  <td>{item.name}</td>
                  <td>{item.source_type}</td>
                  <td><span className="badge">{item.status}</span></td>
                  <td>
                    {item.source_type === "TEXT" && (
                      <button type="button" className="btn-link" onClick={() => setIngestId(item.id)}>Ingestar</button>
                    )}
                    <button type="button" className="btn-link" onClick={() => setKnowledgeStatus(item.id, item.status !== "ACTIVA").then(load)}>
                      {item.status === "ACTIVA" ? "Desactivar" : "Activar"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
