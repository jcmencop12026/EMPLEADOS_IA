import { useCallback, useState } from "react";
import { api } from "../api";

type Diagnostico = {
  id: string;
  ips_name: string;
  estado: string;
  resumen_ejecutivo: {
    principales_problemas?: string[];
    impacto_acumulado?: number | string;
    oportunidades_principales?: string[];
    indicadores_criticos?: Record<string, unknown>;
    acciones_prioritarias?: string[];
  };
  calidad_datos: Record<string, { nivel_calidad?: string; registros?: number; campos_faltantes?: string[] }>;
  indicadores: Record<string, { disponible?: boolean; mensaje?: string; [key: string]: unknown }>;
  trazabilidad: Record<string, unknown>;
  hallazgos: Array<{
    id: string;
    titulo: string;
    descripcion: string;
    categoria: string;
    severidad: string;
    confianza: string;
    prioridad?: number;
    impacto_economico?: number;
    causa_probable?: string;
  }>;
  oportunidades: Array<{
    id: string;
    problema: string;
    accion_propuesta: string;
    responsable_sugerido?: string;
    plazo?: string;
    meta?: string;
    confianza: string;
    prioridad?: number;
  }>;
  plan_accion: Array<Array<{ titulo: string; estado: string; responsable?: string }>>;
  especialistas: { asignaciones?: Array<{ employee_name: string; domain: string; score: number }> };
  comparacion_historica: { disponible?: boolean; comparaciones?: Record<string, unknown> };
  experiencia: { casos_similares?: Array<{ ips_name: string; similitud: number }> };
};

function formatMoney(val: unknown): string {
  if (typeof val === "number") return `$${val.toLocaleString("es-CO")}`;
  if (val === "Información insuficiente") return "Información insuficiente";
  return String(val ?? "—");
}

export function DiagnosticoIpsPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [diag, setDiag] = useState<Diagnostico | null>(null);
  const [pregunta, setPregunta] = useState("¿Por qué tengo menos caja si facturé más?");
  const [respuesta, setRespuesta] = useState<Record<string, unknown> | null>(null);

  const ejecutarDemo = useCallback(async () => {
    setLoading(true);
    setError(null);
    setRespuesta(null);
    try {
      const datasets = await api<Record<string, unknown[]>>("/api/salud/demo/datasets");
      const res = await api<{ id: string }>("/api/salud/analisis", {
        method: "POST",
        body: JSON.stringify({
          ips_name: "IPS Demo Salud",
          request_text: "Analiza la situación financiera y operativa de esta IPS.",
          inline_datasets: datasets,
        }),
      });
      const full = await api<Diagnostico>(`/api/salud/diagnostico/${res.id}`);
      setDiag(full);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al ejecutar análisis");
    } finally {
      setLoading(false);
    }
  }, []);

  async function preguntar() {
    if (!diag) return;
    try {
      const res = await api<Record<string, unknown>>(`/api/salud/pregunta/${diag.id}`, {
        method: "POST",
        body: JSON.stringify({ pregunta }),
      });
      setRespuesta(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al responder");
    }
  }

  return (
    <div className="ops-page">
      <header className="page-header">
        <h1>Diagnóstico IPS</h1>
        <p className="muted">Motor especializado · Análisis financiero y operativo</p>
      </header>

      <section className="panel ops-main">
        <button type="button" className="btn primary" disabled={loading} onClick={ejecutarDemo}>
          {loading ? "Analizando…" : "Ejecutar diagnóstico con datos demo"}
        </button>
        {error && <p className="error-text">{error}</p>}
      </section>

      {diag && (
        <>
          <section className="panel">
            <h2>1. Resumen ejecutivo</h2>
            <ul>
              {(diag.resumen_ejecutivo.principales_problemas ?? []).map((p) => (
                <li key={p}>{p}</li>
              ))}
            </ul>
            <p><strong>Impacto acumulado:</strong> {formatMoney(diag.resumen_ejecutivo.impacto_acumulado)}</p>
            <p><strong>Acciones prioritarias:</strong></p>
            <ul>
              {(diag.resumen_ejecutivo.acciones_prioritarias ?? []).map((a) => (
                <li key={a}>{a}</li>
              ))}
            </ul>
          </section>

          <section className="panel">
            <h2>2. Calidad de datos</h2>
            <table className="data-table">
              <thead>
                <tr><th>Fuente</th><th>Registros</th><th>Calidad</th><th>Campos faltantes</th></tr>
              </thead>
              <tbody>
                {Object.entries(diag.calidad_datos).map(([fuente, q]) => (
                  <tr key={fuente}>
                    <td>{fuente}</td>
                    <td>{q.registros ?? 0}</td>
                    <td>{q.nivel_calidad ?? "—"}</td>
                    <td>{(q.campos_faltantes ?? []).join(", ") || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="panel">
            <h2>3. Indicadores</h2>
            <div className="indicators-grid">
              {Object.entries(diag.indicadores).filter(([k]) => k !== "disponibles" && k !== "no_disponibles").map(([key, val]) => (
                <div key={key} className="indicator-card">
                  <h3>{key}</h3>
                  {val.disponible === false ? (
                    <p className="muted">{val.mensaje ?? "Información insuficiente"}</p>
                  ) : (
                    <pre>{JSON.stringify(val, null, 2).slice(0, 300)}</pre>
                  )}
                </div>
              ))}
            </div>
          </section>

          <section className="panel">
            <h2>4. Hallazgos</h2>
            <table className="data-table">
              <thead>
                <tr><th>Título</th><th>Severidad</th><th>Confianza</th><th>Prioridad</th><th>Impacto</th></tr>
              </thead>
              <tbody>
                {diag.hallazgos.map((h) => (
                  <tr key={h.id}>
                    <td>{h.titulo}</td>
                    <td>{h.severidad}</td>
                    <td>{h.confianza}</td>
                    <td>{h.prioridad?.toFixed(1) ?? "—"}</td>
                    <td>{formatMoney(h.impacto_economico)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="panel">
            <h2>5. Oportunidades</h2>
            {diag.oportunidades.map((o) => (
              <div key={o.id} className="opportunity-card">
                <h3>{o.problema}</h3>
                <p>{o.accion_propuesta}</p>
                <p className="muted">
                  {o.responsable_sugerido} · {o.plazo} · Confianza: {o.confianza}
                </p>
              </div>
            ))}
          </section>

          <section className="panel">
            <h2>6. Plan de acción</h2>
            {diag.plan_accion.length === 0 ? (
              <p className="muted">Seleccione oportunidades para generar un plan de acción.</p>
            ) : (
              diag.plan_accion.flat().map((t, i) => (
                <div key={i}>{t.titulo} — {t.estado} ({t.responsable})</div>
              ))
            )}
          </section>

          <section className="panel">
            <h2>7. Seguimiento</h2>
            <p className="muted">Trazabilidad de valores:</p>
            <pre>{JSON.stringify(diag.trazabilidad, null, 2)}</pre>
          </section>

          <section className="panel">
            <h2>8. Experiencia</h2>
            <p>Especialistas asignados:</p>
            <ul>
              {(diag.especialistas.asignaciones ?? []).map((s) => (
                <li key={s.employee_name}>{s.employee_name} ({s.domain}) — puntaje {s.score}</li>
              ))}
            </ul>
            <p>Casos similares: {(diag.experiencia.casos_similares ?? []).length}</p>
            <div className="ops-actions" style={{ marginTop: "1rem" }}>
              <input
                className="ops-input"
                value={pregunta}
                onChange={(e) => setPregunta(e.target.value)}
                placeholder="Escriba una pregunta…"
              />
              <button type="button" className="btn" onClick={preguntar}>Preguntar</button>
            </div>
            {respuesta && (
              <div className="panel" style={{ marginTop: "0.5rem" }}>
                <p>{String(respuesta.respuesta)}</p>
                <p className="muted">Incertidumbre: {String(respuesta.incertidumbre)}</p>
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
