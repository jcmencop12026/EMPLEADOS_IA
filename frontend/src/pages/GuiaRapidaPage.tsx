import { Link } from "react-router-dom";
import { ContextualHelp } from "../components/ContextualHelp";
import { GUIA_PASOS, HELP_GUIA_RAPIDA } from "../lib/guiaRapidaHelp";
import { usePageAssistantContext } from "../hooks/usePageAssistantContext";

export function GuiaRapidaPage() {
  usePageAssistantContext({ module: "guia_rapida" });

  return (
    <div className="ops-page guia-rapida-page">
      <header className="page-header compact">
        <div className="page-header-row">
          <div>
            <h1>Guía rápida — Primer ejercicio EIAAX</h1>
            <p className="muted">
              Recorrido operativo mínimo para comprender el ciclo completo sin conocer la arquitectura interna.
            </p>
          </div>
          <ContextualHelp content={HELP_GUIA_RAPIDA} />
        </div>
      </header>

      <section className="panel compact-panel guia-intro">
        <p>
          EIAAX entiende la necesidad, solicita información, diagnostica, propone solución, ejecuta con su autorización,
          mide resultados y recomienda mejoras. Use esta guía como mapa; cada paso enlaza a la pantalla correspondiente.
        </p>
      </section>

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
