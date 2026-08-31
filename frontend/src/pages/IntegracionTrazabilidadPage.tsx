import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { fetchIntegrationTrace, type IntegrationTraceStep } from "../api";
import { formatTs, sanitizeDetail } from "./integrationLabels";

export function IntegracionTrazabilidadPage() {
  const [params, setParams] = useSearchParams();
  const [cid, setCid] = useState(params.get("cid") ?? "");
  const [pasos, setPasos] = useState<IntegrationTraceStep[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const q = params.get("cid");
    if (q) {
      setCid(q);
      void loadTrace(q);
    }
  }, [params]);

  async function loadTrace(id: string) {
    const trimmed = id.trim();
    if (!trimmed) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetchIntegrationTrace(trimmed);
      setPasos(res.pasos);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo cargar la trazabilidad");
      setPasos([]);
    } finally {
      setLoading(false);
    }
  }

  function onBuscar(e: React.FormEvent) {
    e.preventDefault();
    setParams(cid.trim() ? { cid: cid.trim() } : {});
    void loadTrace(cid);
  }

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Trazabilidad de integración</h1>
          <p className="muted">
            Siga un correlation_id a través de identidad, catálogo, política, gobierno, validación previa, ejecución, linaje, auditoría y continuidad.
          </p>
        </div>
        <Link className="btn" to="/integraciones">Volver a integraciones</Link>
      </header>

      <section className="card">
        <form className="toolbar" onSubmit={onBuscar}>
          <input
            placeholder="ID de correlación"
            value={cid}
            onChange={(e) => setCid(e.target.value)}
            style={{ minWidth: "320px" }}
          />
          <button type="submit" className="btn primary" disabled={loading}>Buscar</button>
        </form>
        {error && <div className="alert alert-error">{error}</div>}
        {loading && <p className="muted">Cargando cadena…</p>}
        {!loading && pasos.length === 0 && !error && (
          <p className="muted">Ingrese un correlation_id para ver la cadena.</p>
        )}
        {pasos.length > 0 && (
          <table className="data-table compact" style={{ marginTop: "1rem" }}>
            <thead>
              <tr>
                <th>Etapa</th>
                <th>Origen</th>
                <th>Estado</th>
                <th>Detalle</th>
                <th>Marca temporal</th>
              </tr>
            </thead>
            <tbody>
              {pasos.map((p, i) => (
                <tr key={`${p.referencia}-${i}`}>
                  <td><strong>{p.etapa}</strong></td>
                  <td className="mono-sm">{p.origen}</td>
                  <td>{p.estado}</td>
                  <td className="truncate" title={p.detalle}>{sanitizeDetail(p.detalle)}</td>
                  <td>{formatTs(p.timestamp)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
