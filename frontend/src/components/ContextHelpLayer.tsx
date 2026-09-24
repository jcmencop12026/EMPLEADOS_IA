import { useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router-dom";

const HELP_KEY = "eiaax_help_collapsed";
const HELP_TOPICS = [
  ["Centro de Control", "Consola maestra para ver contexto, prioridades, valor, hallazgos y siguiente acción."],
  ["Empresas y prospectos", "Permite seleccionar una empresa o prospecto y conservar ese contexto en todo el análisis."],
  ["Evaluación", "Proceso para conocer la empresa, solicitar información, validar datos y construir hallazgos y oportunidades."],
  ["Oportunidades", "Iniciativas detectadas por EIAAX con prioridad, valor potencial, evidencia y siguiente acción."],
  ["Valor", "Estimación y seguimiento del impacto económico potencial, aprobado, materializado y realizado."],
  ["Empleados IA", "Capacidades digitales configuradas para ejecutar, apoyar o supervisar procesos definidos."],
  ["Implementación", "Convierte una decisión aprobada en alcance, tareas, responsables, integraciones, indicadores y seguimiento."],
  ["PIIAX", "Capa de integración y automatización que conecta sistemas, datos, APIs y flujos requeridos por EIAAX."],
  ["Espacio externo", "Portal seguro para que prospectos o clientes consulten información autorizada y entreguen datos solicitados."],
  ["Publicación", "Controla qué contenido interno puede hacerse visible al cliente o prospecto autorizado."],
  ["Presentación", "Vista ejecutiva y comercial para comunicar hallazgos, oportunidades, valor, compromisos y decisiones."],
  ["Requisitos", "Información requerida para completar y elevar la confianza del análisis de una empresa."],
];

function resolveHelpTarget(target: EventTarget | null): HTMLElement | null {
  return target instanceof HTMLElement ? target.closest<HTMLElement>("[data-help]") : null;
}
export function ContextHelpLayer() {
  const location = useLocation();
  const [help, setHelp] = useState("Pase el cursor sobre una opción para conocer su propósito y efecto.");
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem(HELP_KEY) === "1");
  const [query, setQuery] = useState("");

  useEffect(() => {
    const externalPortal = location.pathname.startsWith("/mi-espacio");
    localStorage.setItem(HELP_KEY, collapsed ? "1" : "0");
    document.documentElement.classList.toggle("eiaax-help-open", !externalPortal && !collapsed);
    return () => document.documentElement.classList.remove("eiaax-help-open");
  }, [collapsed, location.pathname]);

  useEffect(() => {
    function show(target: HTMLElement) {
      const text = target.dataset.help?.trim();
      if (text) setHelp(text);
    }
    function onMouseOver(event: MouseEvent) {
      const target = resolveHelpTarget(event.target);
      if (target) show(target);
    }
    function onFocusIn(event: FocusEvent) {
      const target = resolveHelpTarget(event.target);
      if (target) show(target);
    }
    document.addEventListener("mouseover", onMouseOver);
    document.addEventListener("focusin", onFocusIn);
    return () => {
      document.removeEventListener("mouseover", onMouseOver);
      document.removeEventListener("focusin", onFocusIn);
    };
  }, []);
  const results = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return [];
    return HELP_TOPICS.filter(([title, body]) => `${title} ${body}`.toLowerCase().includes(needle)).slice(0, 6);
  }, [query]);

  if (location.pathname.startsWith("/mi-espacio")) return null;

  if (collapsed) {
    return (
      <button className="eiaax-help-launcher" type="button" onClick={() => setCollapsed(false)} aria-label="Mostrar ayuda">
        ? Ayuda
      </button>
    );
  }

  return (
    <aside className="eiaax-help-layer" aria-label="Ayuda de la plataforma">
      <div className="eiaax-help-layer__head">
        <div><span>AYUDA</span><strong>Plataforma EIAAX</strong></div>
        <button type="button" onClick={() => setCollapsed(true)} aria-label="Colapsar ayuda">×</button>
      </div>
      <input
        className="eiaax-help-search"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Buscar concepto..."
        aria-label="Buscar en la ayuda de EIAAX"
      />
      {query.trim() ? (
        <div className="eiaax-help-results">
          {results.length ? results.map(([title, body]) => (
            <button key={title} type="button" onClick={() => { setHelp(`${title}: ${body}`); setQuery(""); }}>
              <strong>{title}</strong><span>{body}</span>
            </button>
          )) : <p>No encontré ese concepto en la ayuda disponible.</p>}
        </div>
      ) : null}
      <div className="eiaax-help-layer__body">{help}</div>
      <div className="eiaax-help-layer__tip">
        Pase el cursor sobre una opción de la pantalla para ver ayuda contextual, o escriba arriba un concepto de la plataforma.
      </div>
    </aside>
  );
}
