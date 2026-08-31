import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchInformeImpacto, type InformeImpacto } from "../api";
import { ContextualHelp } from "../components/ContextualHelp";
import type { ContextualHelpContent } from "../components/ContextualHelp";

const HELP_INFORME: ContextualHelpContent = {
  screen: "Informe de impacto",
  purpose: "Narrativa determinística que responde qué ocurrió, por qué, quién intervino, cómo, cuándo, cuánto impactó y qué sigue.",
  expected: "Informe legible en español con distinción clara entre PROYECTADO y REAL.",
};

export function InformeImpactoPage() {
  const { informeId } = useParams<{ informeId: string }>();
  const [informe, setInforme] = useState<InformeImpacto | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!informeId) return;
    fetchInformeImpacto(informeId)
      .then(setInforme)
      .catch((e) => setError(e instanceof Error ? e.message : "Error"));
  }, [informeId]);

  if (!informeId) return <p className="error">Informe no especificado</p>;
  if (error) return <p className="error">{error}</p>;
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

      <article className="panel compact-panel informe-narrativa">
        {informe.narrativa.split("\n").map((line, i) => {
          if (line.startsWith("## ")) return <h2 key={i}>{line.slice(3)}</h2>;
          if (line.startsWith("> ")) return <p key={i} className="warning-text">{line.slice(2)}</p>;
          if (!line.trim()) return <br key={i} />;
          return <p key={i}>{line}</p>;
        })}
      </article>

      {informe.expediente_id && (
        <Link to={`/resultados?expediente_id=${informe.expediente_id}`} className="btn">
          Ver indicadores del expediente
        </Link>
      )}
    </div>
  );
}
