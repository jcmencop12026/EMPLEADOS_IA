import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  fetchCommCentroResumen,
  fetchInformesComercialesConfig,
  fetchInformesImpacto,
  fetchInformesPeriodicosPlantillas,
  type CommCentroResumen,
  type InformeComercialConfig,
  type InformeImpacto,
} from "../../api";

type Props = {
  expedienteId: string;
};

export function CabinaInformesPanel({ expedienteId }: Props) {
  const [informes, setInformes] = useState<InformeImpacto[]>([]);
  const [comerciales, setComerciales] = useState<InformeComercialConfig[]>([]);
  const [plantillas, setPlantillas] = useState<Array<Record<string, unknown>>>([]);
  const [comm, setComm] = useState<CommCentroResumen | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetchInformesImpacto(expedienteId).then((r) => setInformes(r.items)),
      fetchInformesComercialesConfig().then((r) => setComerciales(r.items)).catch(() => undefined),
      fetchInformesPeriodicosPlantillas().then((r) => setPlantillas(r.plantillas)).catch(() => undefined),
      fetchCommCentroResumen().then(setComm).catch(() => undefined),
    ]).finally(() => setLoading(false));
  }, [expedienteId]);

  const ultimo = informes[0];

  return (
    <div className="cabina-informes-panel">
      <section className="panel compact-panel">
        <h2>Informes y comunicaciones</h2>
        <p className="muted small">
          Narrativa ejecutiva: qué encontramos, por qué importa, qué proponemos, qué mejoró y qué sigue.
        </p>
        {loading && <p className="muted">Cargando informes…</p>}
        {!loading && !ultimo && (
          <div className="empty-inline">
            <p className="muted">Aún no hay informes generados para este expediente.</p>
            <div className="ops-actions">
              <Link className="btn primary small" to={`/presentacion/${expedienteId}`}>Generar presentación</Link>
              <Link className="btn secondary small" to="/comunicaciones">Programar informe</Link>
            </div>
          </div>
        )}
        {ultimo && (
          <dl className="detail-grid compact">
            <dt>Último informe</dt><dd>{ultimo.titulo ?? ultimo.tipo ?? "—"}</dd>
            <dt>Fecha</dt><dd>{ultimo.created_at ? new Date(ultimo.created_at).toLocaleString("es-CO") : "—"}</dd>
            <dt>Tipo</dt><dd>{String(ultimo.tipo ?? "—")}</dd>
            <dt>Versión</dt><dd>{String(ultimo.version ?? "—")}</dd>
          </dl>
        )}
        {comm && (
          <dl className="detail-grid compact">
            <dt>Envíos periodo</dt><dd>{comm.enviadas ?? "—"}</dd>
            <dt>Pendientes</dt><dd>{comm.pendientes ?? "—"}</dd>
            <dt>Fallidos</dt><dd>{comm.fallidas ?? "—"}</dd>
            <dt>Programados</dt><dd>{comm.programadas ?? "—"}</dd>
          </dl>
        )}
        <div className="ops-actions">
          <Link className="btn primary small" to={`/presentacion/${expedienteId}`}>Ver / generar presentación</Link>
          <Link className="btn secondary small" to={`/informes-impacto?expediente=${expedienteId}`}>Informes de impacto</Link>
          <Link className="btn secondary small" to="/comunicaciones">Centro de comunicaciones</Link>
          <Link className="btn secondary small" to="/demo/informes-periodicos">Informes periódicos</Link>
        </div>
      </section>

      {informes.length > 0 && (
        <section className="panel compact-panel">
          <h3>Informes del expediente</h3>
          <table className="data-table compact-table">
            <thead>
              <tr><th>Título</th><th>Tipo</th><th>Versión</th><th>Fecha</th><th></th></tr>
            </thead>
            <tbody>
              {informes.map((inf) => (
                <tr key={inf.id}>
                  <td>{inf.titulo ?? "—"}</td>
                  <td>{String(inf.tipo ?? "—")}</td>
                  <td>{String(inf.version ?? "—")}</td>
                  <td>{inf.created_at ? new Date(inf.created_at).toLocaleDateString("es-CO") : "—"}</td>
                  <td><Link to={`/informes-impacto/${inf.id}`}>Ver</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {comerciales.length > 0 && (
        <section className="panel compact-panel">
          <h3>Programación comercial</h3>
          <ul className="compact-list">
            {comerciales.slice(0, 5).map((c) => (
              <li key={c.id}>
                {c.nombre ?? c.audiencia ?? "Informe"} — {c.periodicidad ?? "—"}
              </li>
            ))}
          </ul>
        </section>
      )}

      {plantillas.length > 0 && (
        <p className="muted small">{plantillas.length} plantilla(s) periódica(s) disponibles en comunicaciones.</p>
      )}
    </div>
  );
}
