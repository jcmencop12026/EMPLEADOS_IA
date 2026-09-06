type Props = {
  value: unknown;
  title?: string;
};

const FIELD_LABELS: Record<string, string> = {
  titulo: "Título",
  tipo_oportunidad: "Tipo",
  source_reference: "Referencia de origen",
  evidencia: "Evidencia",
  hallazgo: "Hallazgo",
  descripcion: "Descripción",
  confianza: "Confianza",
  fecha: "Fecha",
  expediente_id: "Expediente",
  dominio: "Dominio",
  nota: "Nota",
};

function humanizeKey(key: string): string {
  return FIELD_LABELS[key] ?? key.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase());
}

function renderValue(v: unknown): string {
  if (v == null) return "—";
  if (typeof v === "boolean") return v ? "Sí" : "No";
  if (typeof v === "number") return v.toLocaleString("es-CO");
  if (typeof v === "string") return v.trim() || "—";
  if (Array.isArray(v)) return v.length ? `${v.length} elemento(s)` : "—";
  return "Ver detalle";
}

export function StructuredEvidenceView({ value, title }: Props) {
  if (value == null) {
    return <p className="muted empty-state-inline">Sin evidencia registrada para esta oportunidad.</p>;
  }
  if (typeof value === "string") {
    return (
      <section className="evidencia-structured">
        {title && <h3 className="section-title">{title}</h3>}
        <p>{value}</p>
      </section>
    );
  }
  if (typeof value !== "object") {
    return <p>{String(value)}</p>;
  }
  const entries = Object.entries(value as Record<string, unknown>).filter(
    ([, v]) => v !== null && v !== undefined && v !== "",
  );
  if (entries.length === 0) {
    return <p className="muted">Evidencia registrada sin campos visibles.</p>;
  }
  return (
    <section className="evidencia-structured">
      {title && <h3 className="section-title">{title}</h3>}
      <dl className="detail-grid evidencia-grid">
        {entries.map(([key, val]) => (
          <div key={key} className="evidencia-row">
            <dt>{humanizeKey(key)}</dt>
            <dd>
              {typeof val === "object" && val !== null ? (
                <details className="evidencia-nested">
                  <summary>{renderValue(val)}</summary>
                  <pre className="json-block technical-only">{JSON.stringify(val, null, 2)}</pre>
                </details>
              ) : (
                renderValue(val)
              )}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
