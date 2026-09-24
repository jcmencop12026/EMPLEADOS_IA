import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  entregarInformeImpacto,
  fetchCommChannels,
  fetchEntregasInforme,
  fetchInformeImpacto,
  type CommChannel,
  type InformeImpacto,
} from "../api";
import { ContextualHelp } from "../components/ContextualHelp";
import { usePermissions } from "../hooks/usePermissions";
import { HELP_ENTREGA_INFORME } from "../lib/comunicacionesHelp";
import type { ContextualHelpContent } from "../components/ContextualHelp";

const HELP_INFORME: ContextualHelpContent = {
  screen: "Informe de impacto",
  purpose: "Narrativa determinística que responde qué ocurrió, por qué, quién intervino, cómo, cuándo, cuánto impactó y qué sigue.",
  expected: "Informe legible en español con distinción clara entre PROYECTADO y REAL.",
};

export function InformeImpactoPage() {
  const { has } = usePermissions();
  const { informeId } = useParams<{ informeId: string }>();
  const [informe, setInforme] = useState<InformeImpacto | null>(null);
  const [channels, setChannels] = useState<CommChannel[]>([]);
  const [entregas, setEntregas] = useState<Array<Record<string, unknown>>>([]);
  const [channelId, setChannelId] = useState("");
  const [destId, setDestId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!informeId) return;
    fetchInformeImpacto(informeId)
      .then(setInforme)
      .catch((e) => setError(e instanceof Error ? e.message : "Error"));
    if (has("communications.view")) {
      fetchCommChannels().then((ch) => {
        setChannels(ch);
        const interno = ch.find((c) => c.tipo === "INTERNO_PLATAFORMA");
        if (interno) setChannelId(interno.id);
      });
      fetchEntregasInforme(informeId).then(setEntregas).catch(() => undefined);
    }
  }, [informeId, has]);

  async function onEntregar() {
    if (!informeId || !channelId || !destId) {
      setError("Seleccione canal y destinatario.");
      return;
    }
    try {
      const res = await entregarInformeImpacto(informeId, {
        channel_id: channelId,
        destinatario_tipo: "USUARIO",
        destinatario_id: destId,
        visibilidad_entrega: informe?.visibilidad === "INTERNO" ? "INTERNO" : "VISIBLE_ENTIDAD",
      });
      setMsg(`Entrega registrada — estado: ${res.message.estado}`);
      setEntregas(await fetchEntregasInforme(informeId));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo entregar el informe");
    }
  }

  if (!informeId) return <p className="error">Informe no especificado</p>;
  if (error && !informe) return <p className="error">{error}</p>;
  if (!informe) return <p className="muted">Cargando informe…</p>;

  return (
    <div className="ops-page">
      <header className="page-header">
        <div className="page-header-row">
          <div>
            <Link to="/resultados" className="muted">
              ← Inteligencia de resultados
            </Link>
            <h1>{informe.titulo}</h1>
            <p className="muted">
              {informe.tipo} · versión {informe.version} · {informe.visibilidad}
            </p>
          </div>
          <ContextualHelp content={HELP_INFORME} />
        </div>
      </header>

      {error && <p className="error">{error}</p>}
      {msg && <p className="success">{msg}</p>}

      <article className="panel compact-panel informe-narrativa">
        {informe.narrativa.split("\n").map((line, i) => {
          if (line.startsWith("## ")) return <h2 key={i}>{line.slice(3)}</h2>;
          if (line.startsWith("> ")) return <p key={i} className="warning-text">{line.slice(2)}</p>;
          if (!line.trim()) return <br key={i} />;
          return <p key={i}>{line}</p>;
        })}
      </article>

      {has("communications.send") && (
        <section className="panel compact-panel">
          <div className="page-header-row">
            <h2>Entregar informe</h2>
            <ContextualHelp content={HELP_ENTREGA_INFORME} />
          </div>
          <div className="filters-row">
            <label>
              Canal
              <select value={channelId} onChange={(e) => setChannelId(e.target.value)}>
                <option value="">Seleccione…</option>
                {channels.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nombre} ({c.tipo})
                  </option>
                ))}
              </select>
            </label>
            <label>
              ID destinatario (usuario)
              <input value={destId} onChange={(e) => setDestId(e.target.value)} placeholder="UUID usuario" />
            </label>
            <button type="button" className="btn primary" onClick={onEntregar}>
              Enviar / notificar
            </button>
          </div>
          {informe.visibilidad === "INTERNO" && (
            <p className="warning-text small">Informe INTERNO: solo entrega interna autorizada.</p>
          )}
        </section>
      )}

      {entregas.length > 0 && (
        <section className="panel compact-panel">
          <h2>Historial de entregas</h2>
          <ul className="vista-entidad-list compact">
            {entregas.map((e) => (
              <li key={String(e.id)}>
                Versión {String(e.informe_version)} · {String(e.visibilidad_entrega)} ·{" "}
                {e.created_at ? new Date(String(e.created_at)).toLocaleString("es-CO") : ""}
              </li>
            ))}
          </ul>
        </section>
      )}

      {informe.expediente_id && (
        <Link to={`/resultados?expediente_id=${informe.expediente_id}`} className="btn">
          Ver indicadores del expediente
        </Link>
      )}
    </div>
  );
}
