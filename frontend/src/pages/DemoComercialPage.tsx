import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  fetchDemoComercialManifest,
  seedDemoComercial,
  type DemoComercialManifest,
} from "../api";
import { ContextualHelp } from "../components/ContextualHelp";
import { DemoBanner } from "../components/DemoBanner";
import { usePermissions } from "../hooks/usePermissions";
import { HELP_DEMO_COMERCIAL } from "../lib/demoComercialHelp";

type DemoStep = {
  titulo: string;
  descripcion: string;
  to: string;
  externo?: boolean;
};

export function DemoComercialPage() {
  const { has } = usePermissions();
  const [manifest, setManifest] = useState<DemoComercialManifest | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [seeding, setSeeding] = useState(false);
  const [areaSel, setAreaSel] = useState("facturacion");

  const load = useCallback(() => {
    setLoading(true);
    fetchDemoComercialManifest()
      .then(setManifest)
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar demo"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function onSeed() {
    setSeeding(true);
    try {
      const m = await seedDemoComercial();
      setManifest(m);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo preparar la demo");
    } finally {
      setSeeding(false);
    }
  }

  const enlaces = manifest?.enlaces ?? {};
  const pasos: DemoStep[] = [
    {
      titulo: "1. Contexto y problema",
      descripcion: manifest?.problema ?? "Problema operativo ficticio en salud IPS",
      to: enlaces.diagnostico_ips ?? "/salud/diagnostico",
    },
    {
      titulo: "2. Evaluación y hallazgos",
      descripcion: "Expediente demo con hallazgos visibles para la entidad",
      to: enlaces.evaluacion ?? "/evaluaciones",
    },
    {
      titulo: "3. Indicadores ANTES / PROYECTADO / REAL",
      descripcion: "Inteligencia de resultados con mediciones simuladas",
      to: enlaces.resultados ?? "/resultados",
    },
    {
      titulo: "4. Informe de impacto",
      descripcion: "Narrativa ejecutiva: qué, por qué, cuánto, qué sigue",
      to: enlaces.informe ?? "/resultados",
    },
    {
      titulo: "5. Presentación por audiencia",
      descripcion: "Gerencia, Operación, Sistemas o Financiero — misma fuente, distinto énfasis",
      to: enlaces.presentacion ?? "/demo",
    },
    {
      titulo: "6. Valor y comercial",
      descripcion: "Simulador de valor y propuestas (sin compromiso contractual)",
      to: enlaces.comercial ?? "/comercial",
    },
    {
      titulo: "7. Centro de Control",
      descripcion: "Vista ejecutiva consolidada",
      to: enlaces.centro_control ?? "/",
    },
  ];

  const areaLabel = manifest?.areas?.find((a) => a.id === areaSel)?.label ?? areaSel;

  return (
    <div className="ops-page demo-comercial-page">
      <DemoBanner />

      <header className="page-header">
        <div className="page-header-row">
          <div>
            <h1>Demo comercial EIAAX</h1>
            <p className="muted">
              {manifest?.empresa_ficticia ?? "Empresa ficticia"} — experiencia previa a la evaluación real
            </p>
          </div>
          <ContextualHelp content={HELP_DEMO_COMERCIAL} />
        </div>
      </header>

      {error && <p className="error">{error}</p>}
      {loading && <p className="muted">Cargando demo…</p>}

      {!loading && !manifest?.expediente_id && has("evaluacion.manage") && (
        <section className="panel">
          <h2>Preparar datos de demostración</h2>
          <p className="muted">
            Genera un expediente ficticio aislado (correlation_id DEMO). No afecta datos reales.
          </p>
          <button type="button" className="btn primary" disabled={seeding} onClick={onSeed}>
            {seeding ? "Preparando…" : "Cargar demo ficticia"}
          </button>
        </section>
      )}

      <section className="panel demo-story">
        <h2>Historia de la demo</h2>
        <dl className="detail-dl">
          <dt>Empresa ficticia</dt>
          <dd>{manifest?.empresa_ficticia ?? "Grupo Andina Salud"}</dd>
          <dt>Problema</dt>
          <dd>{manifest?.problema}</dd>
          {manifest?.expediente_codigo && (
            <>
              <dt>Expediente demo</dt>
              <dd className="mono">{manifest.expediente_codigo}</dd>
            </>
          )}
        </dl>
      </section>

      <section className="panel">
        <h2>Recorrido guiado</h2>
        <ol className="demo-steps-list">
          {pasos.map((p) => (
            <li key={p.titulo} className="demo-step-card">
              <h3>{p.titulo}</h3>
              <p>{p.descripcion}</p>
              <Link to={p.to} className="btn">
                Abrir
              </Link>
            </li>
          ))}
        </ol>
      </section>

      <section className="panel demo-cta-evaluar">
        <h2>¿Listo para evaluar su empresa?</h2>
        <p className="muted">
          La demo ilustra posibilidades. El flujo real de evaluación recopila información de su organización.
        </p>
        <label>
          Área o aspecto de interés
          <select value={areaSel} onChange={(e) => setAreaSel(e.target.value)}>
            {(manifest?.areas ?? [{ id: "facturacion", label: "Facturación" }]).map((a) => (
              <option key={a.id} value={a.id}>{a.label}</option>
            ))}
          </select>
        </label>
        <Link
          to={`/evaluaciones?nuevo=1&area=${encodeURIComponent(areaSel)}&area_label=${encodeURIComponent(areaLabel)}`}
          className="btn primary"
        >
          Quiero evaluar mi empresa
        </Link>
      </section>

      <section className="panel">
        <h2>Informes periódicos</h2>
        <p className="muted">
          Configure resúmenes diarios, semanales, mensuales o por evento según audiencia.
        </p>
        <Link to="/demo/informes-periodicos" className="btn">
          Ver configuración de informes
        </Link>
      </section>
    </div>
  );
}
