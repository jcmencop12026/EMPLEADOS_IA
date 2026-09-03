import { Link } from "react-router-dom";

type Item = {
  label: string;
  to: string;
  desc?: string;
};

type Props = {
  expedienteId?: string;
  /** Sin encabezado duplicado cuando va dentro de &lt;details&gt;. */
  embedded?: boolean;
};

function withContext(path: string, expedienteId?: string): string {
  if (!expedienteId) return path;
  const sep = path.includes("?") ? "&" : "?";
  if (path.includes("expediente=") || path.includes("evaluacionId")) return path;
  if (path.startsWith("/evaluaciones/")) return path;
  if (path === "/evaluaciones") return `${path}?q=${expedienteId}`;
  return `${path}${sep}expediente=${expedienteId}`;
}

const GROUPS: Array<{ title: string; items: Item[] }> = [
  {
    title: "Empresas y evaluación",
    items: [
      { label: "Empresas", to: "/empresas", desc: "Acceso operativo por entidad" },
      { label: "Evaluaciones", to: "/evaluaciones", desc: "Expedientes EIAAX" },
      { label: "Cabina", to: "/evaluaciones/__EXP__", desc: "Puesto de mando empresa" },
      { label: "Información", to: "/evaluaciones/__EXP__?tab=diagnostico", desc: "Datos adaptativos" },
      { label: "Diagnóstico", to: "/evaluaciones/__EXP__?tab=diagnostico", desc: "Hallazgos y análisis" },
    ],
  },
  {
    title: "Solución y operación",
    items: [
      { label: "Oportunidades", to: "/oportunidades" },
      { label: "Solución IA", to: "/evaluaciones/__EXP__?tab=solucion" },
      { label: "Implementación", to: "/implementacion" },
      { label: "Empleados IA", to: "/directorio" },
      { label: "Automatizaciones", to: "/automatizaciones" },
      { label: "Ejecuciones", to: "/ejecuciones" },
      { label: "Aprobaciones", to: "/aprobaciones" },
      { label: "Operaciones", to: "/operaciones" },
    ],
  },
  {
    title: "Valor y relación",
    items: [
      { label: "Valor", to: "/evaluaciones/__EXP__?tab=valor" },
      { label: "Resultados", to: "/evaluaciones/__EXP__?tab=resultados" },
      { label: "Comercial", to: "/evaluaciones/__EXP__?tab=contrato" },
      { label: "Contrato", to: "/evaluaciones/__EXP__?tab=contrato" },
      { label: "Informes", to: "/evaluaciones/__EXP__?tab=informes" },
      { label: "Soporte", to: "/soporte" },
      { label: "Presentación", to: "/presentacion/__EXP__" },
      { label: "Vista Empresa", to: "/evaluaciones/__EXP__?tab=vista-empresa" },
    ],
  },
];

export function CentroControlMasterAccess({ expedienteId, embedded = false }: Props) {
  return (
    <section className={`cc-master-access ${embedded ? "cc-master-access--embedded" : ""}`}>
      {!embedded && (
        <>
          <h2 className="section-title">Accesos de profundidad</h2>
          <p className="muted small">
            {expedienteId
              ? "Navegue el ciclo de la empresa seleccionada."
              : "Módulos detallados bajo demanda."}
          </p>
        </>
      )}
      <div className="cc-master-grid">
        {GROUPS.map((group) => (
          <div key={group.title} className="cc-master-group">
            <h3 className="cc-subtitle">{group.title}</h3>
            <ul className="cc-master-links">
              {group.items.map((item) => {
                const raw = item.to.replace("__EXP__", expedienteId ?? "");
                const to = raw.includes("__EXP__") ? "/evaluaciones" : withContext(raw, expedienteId);
                const disabled = item.to.includes("__EXP__") && !expedienteId;
                return (
                  <li key={`${group.title}-${item.label}`}>
                    {disabled ? (
                      <span className="cc-master-link disabled" title="Seleccione una empresa">
                        {item.label}
                      </span>
                    ) : (
                      <Link to={to} className="cc-master-link">
                        <strong>{item.label}</strong>
                        {item.desc && <span className="muted small">{item.desc}</span>}
                      </Link>
                    )}
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}
