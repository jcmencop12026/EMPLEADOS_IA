import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  createInformeComercialConfig,
  fetchInformesComercialesConfig,
  fetchInformesPeriodicosPlantillas,
  type InformeComercialConfig,
} from "../api";
import { DemoBanner } from "../components/DemoBanner";
import { usePermissions } from "../hooks/usePermissions";
import { AUDIENCIAS } from "../lib/demoComercialHelp";

type Plantilla = {
  periodicidad: string;
  audiencias: string[];
  canal: string;
  contenido_email: string;
  sensible: boolean;
};

const PERIODICIDAD_LABELS: Record<string, string> = {
  DIARIO: "Diario",
  SEMANAL: "Semanal",
  MENSUAL: "Mensual",
  TRIMESTRAL: "Trimestral",
  EVENTO: "Por evento",
};

export function InformesPeriodicosDemoPage() {
  const { has } = usePermissions();
  const [plantillas, setPlantillas] = useState<Plantilla[]>([]);
  const [configs, setConfigs] = useState<InformeComercialConfig[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [form, setForm] = useState({
    nombre: "Resumen ejecutivo comercial",
    audiencia: "GERENCIA",
    periodicidad: "MENSUAL",
    destinatarios: "",
    resumen: "Resumen + enlace seguro al informe",
  });

  useEffect(() => {
    fetchInformesPeriodicosPlantillas()
      .then((r) => setPlantillas(r.plantillas as Plantilla[]))
      .catch((e) => setError(e instanceof Error ? e.message : "Error"));
    if (has("communications.view")) {
      fetchInformesComercialesConfig()
        .then((r) => setConfigs(r.items))
        .catch(() => {
          /* sin permiso o sin config */
        });
    }
  }, [has]);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    if (!has("communications.rule.manage")) return;
    try {
      const created = await createInformeComercialConfig({
        nombre: form.nombre,
        audiencia: form.audiencia,
        periodicidad: form.periodicidad,
        destinatarios: form.destinatarios
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        resumen: form.resumen,
        enlace_seguro: true,
        activo: true,
      });
      setConfigs((prev) => [created, ...prev]);
      setMsg("Configuración guardada — integración MB-11 pendiente de cableado del scheduler.");
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo guardar");
    }
  }

  return (
    <div className="ops-page">
      <DemoBanner />
      <p><Link to="/demo">← Demo comercial</Link></p>
      <header className="page-header">
        <h1>Informes periódicos</h1>
        <p className="muted">
          Plantillas comerciales y configuración persistente vía adapter MB-11 (sin segundo motor).
        </p>
      </header>

      {error && <p className="error">{error}</p>}
      {msg && <p className="panel muted-box">{msg}</p>}

      <table className="data-table compact-table">
        <thead>
          <tr>
            <th>Periodicidad</th>
            <th>Audiencias</th>
            <th>Canal</th>
            <th>Contenido email</th>
            <th>Sensible</th>
          </tr>
        </thead>
        <tbody>
          {plantillas.map((p) => (
            <tr key={p.periodicidad}>
              <td>{PERIODICIDAD_LABELS[p.periodicidad] ?? p.periodicidad}</td>
              <td>
                {p.audiencias.map((a) => AUDIENCIAS.find((x) => x.id === a)?.label ?? a).join(", ")}
              </td>
              <td>{p.canal.replace(/_/g, " ")}</td>
              <td>{p.contenido_email}</td>
              <td>{p.sensible ? "Enlace seguro" : "Resumen en bandeja"}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {has("communications.rule.manage") && (
        <form className="panel compact-panel" onSubmit={onCreate}>
          <h2>Nueva configuración comercial</h2>
          <div className="form-grid">
            <label>
              Nombre
              <input required value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} />
            </label>
            <label>
              Audiencia
              <select value={form.audiencia} onChange={(e) => setForm({ ...form, audiencia: e.target.value })}>
                {AUDIENCIAS.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Periodicidad
              <select
                value={form.periodicidad}
                onChange={(e) => setForm({ ...form, periodicidad: e.target.value })}
              >
                {Object.entries(PERIODICIDAD_LABELS).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Destinatarios (correos, separados por coma)
              <input
                value={form.destinatarios}
                onChange={(e) => setForm({ ...form, destinatarios: e.target.value })}
                placeholder="ejecutivo@empresa.com"
              />
            </label>
            <label className="full-width">
              Resumen
              <textarea value={form.resumen} onChange={(e) => setForm({ ...form, resumen: e.target.value })} rows={2} />
            </label>
          </div>
          <button type="submit" className="btn primary">
            Guardar configuración
          </button>
        </form>
      )}

      {configs.length > 0 && (
        <section className="panel">
          <h2>Configuraciones activas</h2>
          <table className="data-table compact-table">
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Audiencia</th>
                <th>Frecuencia</th>
                <th>Activo</th>
                <th>Próximo envío</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {configs.map((c) => (
                <tr key={c.id}>
                  <td>{c.nombre}</td>
                  <td>{c.audiencia}</td>
                  <td>{PERIODICIDAD_LABELS[c.periodicidad] ?? c.periodicidad}</td>
                  <td>{c.activo ? "Sí" : "No"}</td>
                  <td>{c.proximo_envio ? new Date(c.proximo_envio).toLocaleString("es-CO") : "—"}</td>
                  <td>{c.estado}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      <section className="panel">
        <h2>Entrega segura</h2>
        <p className="muted">
          Los informes con visibilidad INTERNO no se envían por correo con datos completos.
          Use el Centro de Información para entregar con trazabilidad.
        </p>
        <Link to="/comunicaciones" className="btn">
          Ir a Centro de Información
        </Link>
      </section>
    </div>
  );
}
