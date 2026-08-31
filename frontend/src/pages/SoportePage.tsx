import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import type { SupportCase } from "../api";
import {
  createSupportCase,
  fetchSupportAutoservicio,
  fetchSupportCases,
  fetchSupportProblems,
  fetchSupportTipos,
  suggestSupportPriority,
} from "../api";
import { ContextualHelp } from "../components/ContextualHelp";
import { EiaaxTable, type EiaaxColumn } from "../components/EiaaxTable";
import { usePermissions } from "../hooks/usePermissions";
import { ESTADO_ETIQUETAS, HELP_MESA_AYUDA, SLA_ETIQUETAS } from "../lib/soporteHelp";

type Vista = "todos" | "mios" | "proximos" | "vencidos" | "problemas";

export function SoportePage() {
  const { has } = usePermissions();
  const [cases, setCases] = useState<SupportCase[]>([]);
  const [problems, setProblems] = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [estado, setEstado] = useState("");
  const [vista, setVista] = useState<Vista>("todos");
  const [showForm, setShowForm] = useState(false);
  const [showAutoservicio, setShowAutoservicio] = useState(false);
  const [autoservicioQ, setAutoservicioQ] = useState("");
  const [autoservicio, setAutoservicio] = useState<Record<string, unknown> | null>(null);
  const [tipos, setTipos] = useState<string[]>([]);
  const [form, setForm] = useState({
    tipo: "SOLICITUD",
    asunto: "",
    descripcion: "",
    prioridad: "MEDIA",
    impacto: "MEDIO",
    urgencia: "MEDIA",
  });

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    const sla = vista === "proximos" ? "PROXIMO" : vista === "vencidos" ? "VENCIDO" : undefined;
    const soloMios = vista === "mios" || (!has("support.view") && vista !== "problemas");
    if (vista === "problemas") {
      fetchSupportProblems()
        .then(setProblems)
        .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar problemas"))
        .finally(() => setLoading(false));
      return;
    }
    fetchSupportCases({ q: q || undefined, estado: estado || undefined, solo_mios: soloMios, sla_estado: sla })
      .then(setCases)
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar casos"))
      .finally(() => setLoading(false));
  }, [q, estado, vista, has]);

  useEffect(() => {
    load();
    fetchSupportTipos().then((t) => setTipos(t.tipos)).catch(() => undefined);
  }, [load]);

  useEffect(() => {
    if (!form.impacto || !form.urgencia) return;
    suggestSupportPriority(form.impacto, form.urgencia)
      .then((r) => setForm((f) => ({ ...f, prioridad: r.prioridad_sugerida })))
      .catch(() => undefined);
  }, [form.impacto, form.urgencia]);

  async function handleAutoservicio(e: React.FormEvent) {
    e.preventDefault();
    try {
      const res = await fetchSupportAutoservicio(autoservicioQ);
      setAutoservicio(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error en autoservicio");
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    try {
      await createSupportCase(form);
      setShowForm(false);
      setForm({ tipo: "SOLICITUD", asunto: "", descripcion: "", prioridad: "MEDIA", impacto: "MEDIO", urgencia: "MEDIA" });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo crear el caso");
    }
  }

  const columns = useMemo<EiaaxColumn<SupportCase>[]>(
    () => [
      { key: "referencia", label: "Referencia", sortable: true, getValue: (r) => r.referencia },
      { key: "tipo", label: "Tipo", sortable: true, getValue: (r) => r.tipo },
      { key: "asunto", label: "Asunto", sortable: true, getValue: (r) => r.asunto },
      {
        key: "estado",
        label: "Estado",
        sortable: true,
        getValue: (r) => r.estado,
        render: (r) => ESTADO_ETIQUETAS[r.estado] ?? r.estado,
      },
      { key: "prioridad", label: "Prioridad", sortable: true, getValue: (r) => r.prioridad },
      {
        key: "sla",
        label: "SLA",
        sortable: true,
        getValue: (r) => r.sla_estado ?? "",
        render: (r) => (
          <span className={`cc-tag cc-tag-${r.sla_estado === "VENCIDO" ? "inferencia" : r.sla_estado === "PROXIMO" ? "recomendacion" : "hecho"}`}>
            {SLA_ETIQUETAS[r.sla_estado ?? ""] ?? r.sla_estado ?? "—"}
          </span>
        ),
      },
      {
        key: "link",
        label: "",
        render: (r) => <Link to={`/soporte/casos/${r.id}`}>Ver</Link>,
      },
    ],
    [],
  );

  return (
    <div className="ops-page">
      <header className="page-header">
        <div className="page-header-row">
          <div>
            <h1>Mesa de Ayuda</h1>
            <p className="muted">Solicitudes, incidentes, consultas y continuidad operativa</p>
          </div>
          <ContextualHelp content={HELP_MESA_AYUDA} />
        </div>
      </header>

      <nav className="tab-bar compact-toolbar" aria-label="Vistas de soporte">
        {(
          [
            ["todos", "Todos / autorizados"],
            ["mios", "Mis casos"],
            ["proximos", "Próximos a vencer"],
            ["vencidos", "Vencidos"],
            ["problemas", "Problemas"],
          ] as const
        ).map(([key, label]) => (
          <button
            key={key}
            type="button"
            className={vista === key ? "tab active" : "tab"}
            onClick={() => setVista(key)}
          >
            {label}
          </button>
        ))}
      </nav>

      <div className="toolbar compact-toolbar">
        {vista !== "problemas" && (
          <>
            <input
              type="search"
              placeholder="Buscar…"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              aria-label="Buscar casos"
            />
            <select value={estado} onChange={(e) => setEstado(e.target.value)} aria-label="Filtrar por estado">
              <option value="">Todos los estados</option>
              {Object.entries(ESTADO_ETIQUETAS).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </>
        )}
        <button type="button" onClick={load}>Actualizar</button>
        {has("support.create") && (
          <>
            <button type="button" className="btn" onClick={() => { setShowAutoservicio(!showAutoservicio); setShowForm(false); }}>
              ¿Qué necesitas?
            </button>
            <button type="button" className="btn primary" onClick={() => { setShowForm(!showForm); setShowAutoservicio(false); }}>
              {showForm ? "Cancelar" : "Nuevo caso"}
            </button>
          </>
        )}
      </div>

      {error && <p className="error">{error}</p>}

      {showAutoservicio && (
        <section className="panel">
          <h2>Autoservicio — ¿Qué necesitas?</h2>
          <form onSubmit={handleAutoservicio} className="compact-toolbar">
            <input
              required
              value={autoservicioQ}
              onChange={(e) => setAutoservicioQ(e.target.value)}
              placeholder="Describa su necesidad o síntoma…"
              aria-label="Consulta autoservicio"
            />
            <button type="submit" className="btn">Buscar ayuda</button>
          </form>
          {autoservicio && (
            <div className="autoservicio-results">
              <p className="muted">Prioridad sugerida: <strong>{String(autoservicio.prioridad_sugerida)}</strong></p>
              {(autoservicio.articulos as Array<Record<string, string>> | undefined)?.length ? (
                <>
                  <h3>Conocimiento relacionado</h3>
                  <ul>
                    {(autoservicio.articulos as Array<Record<string, string>>).map((a, i) => (
                      <li key={i}>{a.titulo}</li>
                    ))}
                  </ul>
                </>
              ) : null}
              {(autoservicio.casos_similares as Array<Record<string, string>> | undefined)?.length ? (
                <>
                  <h3>Casos similares abiertos</h3>
                  <ul>
                    {(autoservicio.casos_similares as Array<Record<string, string>>).map((c) => (
                      <li key={c.id}><Link to={`/soporte/casos/${c.id}`}>{c.referencia} — {c.asunto}</Link></li>
                    ))}
                  </ul>
                </>
              ) : null}
              <button
                type="button"
                className="btn primary"
                onClick={() => {
                  setForm((f) => ({
                    ...f,
                    asunto: autoservicioQ.slice(0, 120),
                    descripcion: autoservicioQ,
                    impacto: String(autoservicio.impacto_sugerido ?? "MEDIO"),
                    urgencia: String(autoservicio.urgencia_sugerida ?? "MEDIA"),
                  }));
                  setShowForm(true);
                  setShowAutoservicio(false);
                }}
              >
                Crear caso con esta información
              </button>
            </div>
          )}
        </section>
      )}

      {showForm && has("support.create") && (
        <form className="panel" onSubmit={handleCreate}>
          <h2>Nuevo caso</h2>
          <label>
            Tipo
            <select value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value })}>
              {tipos.map((t) => (
                <option key={t} value={t}>{t.replace(/_/g, " ")}</option>
              ))}
            </select>
          </label>
          <label>
            Asunto
            <input required value={form.asunto} onChange={(e) => setForm({ ...form, asunto: e.target.value })} />
          </label>
          <label>
            Descripción
            <textarea required rows={4} value={form.descripcion} onChange={(e) => setForm({ ...form, descripcion: e.target.value })} />
          </label>
          <div className="form-row">
            <label>
              Impacto
              <select value={form.impacto} onChange={(e) => setForm({ ...form, impacto: e.target.value })}>
                <option value="CRITICO">Crítico</option>
                <option value="ALTO">Alto</option>
                <option value="MEDIO">Medio</option>
                <option value="BAJO">Bajo</option>
              </select>
            </label>
            <label>
              Urgencia
              <select value={form.urgencia} onChange={(e) => setForm({ ...form, urgencia: e.target.value })}>
                <option value="CRITICA">Crítica</option>
                <option value="ALTA">Alta</option>
                <option value="MEDIA">Media</option>
                <option value="BAJA">Baja</option>
              </select>
            </label>
            <label>
              Prioridad (sugerida)
              <select value={form.prioridad} onChange={(e) => setForm({ ...form, prioridad: e.target.value })}>
                <option value="CRITICA">Crítica</option>
                <option value="ALTA">Alta</option>
                <option value="MEDIA">Media</option>
                <option value="BAJA">Baja</option>
              </select>
            </label>
          </div>
          <button type="submit" className="btn primary">Crear caso</button>
        </form>
      )}

      {loading ? (
        <p className="muted">Cargando…</p>
      ) : vista === "problemas" ? (
        <table className="data-table compact-table">
          <thead>
            <tr><th>Referencia</th><th>Título</th><th>Estado</th><th>Incidentes</th></tr>
          </thead>
          <tbody>
            {problems.length === 0 ? (
              <tr><td colSpan={4} className="muted">No hay problemas registrados.</td></tr>
            ) : (
              problems.map((p) => (
                <tr key={String(p.id)}>
                  <td className="mono">{String(p.referencia)}</td>
                  <td>{String(p.titulo)}</td>
                  <td>{String(p.estado)}</td>
                  <td>{String(p.incidentes ?? 0)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      ) : (
        <EiaaxTable rows={cases} columns={columns} emptyMessage="No hay casos." />
      )}
    </div>
  );
}
