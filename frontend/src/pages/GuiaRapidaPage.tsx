import { Link } from "react-router-dom";
import { ContextualHelp } from "../components/ContextualHelp";
import { GUIA_PASOS, HELP_GUIA_RAPIDA } from "../lib/guiaRapidaHelp";
import { DEMO_HORIZONTE_ETIQUETA, INSTRUCTIVO_PARTES } from "../lib/instructivoOperativo";
import { usePageAssistantContext } from "../hooks/usePageAssistantContext";
import { useState } from "react";

export function GuiaRapidaPage() {
  usePageAssistantContext({ module: "guia_rapida" });
  const [parte, setParte] = useState(1);

  const activa = INSTRUCTIVO_PARTES.find((p) => p.id === parte) ?? INSTRUCTIVO_PARTES[0];

  return (
    <div className="ops-page guia-rapida-page">
      <header className="page-header compact">
        <div className="page-header-row">
          <div>
            <h1>Instructivo operativo V1</h1>
            <p className="muted">
              Guía mantenible para operar EIAAX sin conocer la arquitectura interna. {DEMO_HORIZONTE_ETIQUETA}
            </p>
          </div>
          <ContextualHelp content={HELP_GUIA_RAPIDA} />
        </div>
      </header>

      <nav className="tab-bar compact-tabs" aria-label="Partes del instructivo">
        {INSTRUCTIVO_PARTES.map((p) => (
          <button
            key={p.id}
            type="button"
            className={`tab-btn ${parte === p.id ? "active" : ""}`}
            onClick={() => setParte(p.id)}
          >
            {p.id}. {p.titulo.split(" ")[0]}
          </button>
        ))}
      </nav>

      <section className="panel compact-panel guia-intro">
        <h2 className="section-title">Parte {activa.id} — {activa.titulo}</h2>
        <p>{activa.resumen}</p>
        <ul className="instructivo-list">
          {activa.puntos.map((pt) => (
            <li key={pt}>{pt}</li>
          ))}
        </ul>
      </section>

      {parte === 2 && (
        <ol className="guia-pasos-list">
          {GUIA_PASOS.map((paso) => (
            <li key={paso.n} className="guia-paso panel compact-panel">
              <div className="guia-paso-num">{paso.n}</div>
              <div className="guia-paso-body">
                <strong>{paso.titulo}</strong>
                <p className="muted small">{paso.detalle}</p>
                <Link to={paso.ruta} className="btn small secondary">Ir al paso</Link>
              </div>
            </li>
          ))}
        </ol>
      )}

      <section className="panel compact-panel">
        <h2 className="section-title">¿Qué sigue?</h2>
        <p className="muted">
          Vuelva al <Link to="/">Centro de Control</Link> para supervisar pendientes, aprobaciones, valor y salud.
          Use el asistente contextual en cualquier pantalla para preguntar qué hacer ahora.
        </p>
      </section>
    </div>
  );
}
