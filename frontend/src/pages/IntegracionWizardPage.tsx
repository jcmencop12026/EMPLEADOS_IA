import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import type { IntegrationCatalogItem } from "../api";
import {
  createIntegrationConnector,
  fetchIntegrationCatalog,
  testIntegrationConnector,
  updateIntegrationConnector,
} from "../api";

const STEPS = [
  "Tipo de conexión",
  "Datos básicos",
  "Autenticación",
  "Origen / destino",
  "Mapeo",
  "Probar conexión",
  "Activar",
];

const AUTH_OPTIONS = [
  { value: "NINGUNA", label: "Sin autenticación" },
  { value: "API_KEY", label: "API Key" },
  { value: "BEARER", label: "Bearer token" },
  { value: "BASIC", label: "Basic" },
  { value: "OAUTH2", label: "OAuth2 (preparado)" },
];

const DEST_OPTIONS = [
  { value: "", label: "Sin destino específico" },
  { value: "SENALES", label: "Señales (1120)" },
  { value: "CONOCIMIENTO", label: "Conocimiento" },
  { value: "AUTOMATIZACIONES", label: "Automatizaciones" },
  { value: "EMPLEADOS_IA", label: "Empleados IA" },
  { value: "PROCESOS", label: "Procesos" },
];

export function IntegracionWizardPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [catalog, setCatalog] = useState<IntegrationCatalogItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [connectorId, setConnectorId] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{ resultado: string; mensaje: string } | null>(null);
  const [webhookToken, setWebhookToken] = useState<string | null>(null);

  const [form, setForm] = useState({
    connector_type: "API_REST",
    code: "",
    name: "",
    descripcion: "",
    auth_type: "NINGUNA",
    secret_env_var: "",
    destination_type: "",
    signal_source_code: "",
    configJson: '{"mock_response": [{"tipo": "integracion", "dominio": "ops", "evento": "evt", "referencia": "ref-1"}]}',
    mappingJson: "[]",
    schemaJson: '{"required": []}',
  });

  useEffect(() => {
    fetchIntegrationCatalog().then(setCatalog).catch(() => undefined);
  }, []);

  function patch<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function ensureCreated(): Promise<string> {
    if (connectorId) return connectorId;
    let config: Record<string, unknown> = {};
    try {
      config = JSON.parse(form.configJson || "{}");
    } catch {
      throw new Error("Configuración JSON no válida");
    }
    const created = await createIntegrationConnector({
      code: form.code,
      name: form.name,
      descripcion: form.descripcion || undefined,
      connector_type: form.connector_type,
      auth_type: form.auth_type,
      secret_env_var: form.secret_env_var || undefined,
      destination_type: form.destination_type || undefined,
      signal_source_code: form.signal_source_code || undefined,
      config,
      generate_webhook_token: form.connector_type === "WEBHOOK",
    });
    setConnectorId(created.id);
    if (created.webhook_token) setWebhookToken(created.webhook_token);
    return created.id;
  }

  async function saveConfig(id: string) {
    let config: Record<string, unknown> = {};
    let mapping: unknown[] = [];
    let schema: Record<string, unknown> = {};
    try {
      config = JSON.parse(form.configJson || "{}");
      mapping = JSON.parse(form.mappingJson || "[]");
      schema = JSON.parse(form.schemaJson || "{}");
    } catch {
      throw new Error("JSON de configuración, mapeo o esquema no válido");
    }
    await updateIntegrationConnector(id, {
      config,
      mapping,
      schema,
      destination_type: form.destination_type || undefined,
      signal_source_code: form.signal_source_code || undefined,
      secret_env_var: form.secret_env_var || undefined,
    });
  }

  async function next() {
    setError(null);
    try {
      if (step === 1) {
        if (!form.code.trim() || !form.name.trim()) {
          setError("Código y nombre son obligatorios");
          return;
        }
        await ensureCreated();
      }
      if (step === 4) {
        const id = await ensureCreated();
        await saveConfig(id);
      }
      if (step === 5) {
        const id = await ensureCreated();
        await saveConfig(id);
        const res = await testIntegrationConnector(id);
        setTestResult(res);
      }
      if (step === 6) {
        const id = await ensureCreated();
        await updateIntegrationConnector(id, { status: "ACTIVO" });
        navigate(`/integraciones/${id}`);
        return;
      }
      setStep((s) => Math.min(s + 1, STEPS.length - 1));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error en el asistente");
    }
  }

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Nueva integración</h1>
          <p className="muted">Asistente de configuración en {STEPS.length} pasos</p>
        </div>
        <Link to="/integraciones" className="btn">
          Volver
        </Link>
      </header>

      {error && <div className="alert alert-error">{error}</div>}

      <ol className="wizard-steps">
        {STEPS.map((label, i) => (
          <li key={label} className={i === step ? "active" : i < step ? "done" : ""}>
            {i + 1}. {label}
          </li>
        ))}
      </ol>

      <section className="card">
        {step === 0 && (
          <>
            <h2>Tipo de conexión</h2>
            <p className="muted">Seleccione el tipo de conector según la fuente externa.</p>
            <select value={form.connector_type} onChange={(e) => patch("connector_type", e.target.value)}>
              {catalog.map((c) => (
                <option key={c.type} value={c.type}>
                  {c.name} — {c.descripcion}
                </option>
              ))}
            </select>
          </>
        )}

        {step === 1 && (
          <>
            <h2>Datos básicos</h2>
            <label>
              Código único
              <input value={form.code} onChange={(e) => patch("code", e.target.value)} placeholder="ej. crm-ventas" />
            </label>
            <label>
              Nombre visible
              <input value={form.name} onChange={(e) => patch("name", e.target.value)} />
            </label>
            <label>
              Descripción
              <textarea value={form.descripcion} onChange={(e) => patch("descripcion", e.target.value)} rows={2} />
            </label>
          </>
        )}

        {step === 2 && (
          <>
            <h2>Autenticación</h2>
            <p className="muted">Las credenciales se almacenan por referencia segura (variable de entorno). Nunca se muestran en pantalla.</p>
            <label>
              Modalidad
              <select value={form.auth_type} onChange={(e) => patch("auth_type", e.target.value)}>
                {AUTH_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </label>
            {form.auth_type !== "NINGUNA" && (
              <label>
                Variable de entorno (referencia)
                <input
                  value={form.secret_env_var}
                  onChange={(e) => patch("secret_env_var", e.target.value)}
                  placeholder="INTEGRACION_MI_API_KEY"
                />
              </label>
            )}
          </>
        )}

        {step === 3 && (
          <>
            <h2>Origen / destino</h2>
            <label>
              Configuración del conector (JSON)
              <textarea value={form.configJson} onChange={(e) => patch("configJson", e.target.value)} rows={8} />
            </label>
            <label>
              Destino de los datos
              <select value={form.destination_type} onChange={(e) => patch("destination_type", e.target.value)}>
                {DEST_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </label>
            {form.destination_type === "SENALES" && (
              <label>
                Código fuente de señal (1120)
                <input
                  value={form.signal_source_code}
                  onChange={(e) => patch("signal_source_code", e.target.value)}
                  placeholder="int-src"
                />
              </label>
            )}
            {webhookToken && (
              <p className="muted">
                Token webhook (mostrado una sola vez): <code>{webhookToken}</code>
              </p>
            )}
          </>
        )}

        {step === 4 && (
          <>
            <h2>Mapeo de datos</h2>
            <p className="muted">Reglas simples: renombrar, valor fijo, concatenar, conversión de tipo.</p>
            <label>
              Mapeo (JSON)
              <textarea value={form.mappingJson} onChange={(e) => patch("mappingJson", e.target.value)} rows={6} />
            </label>
            <label>
              Esquema de validación (JSON)
              <textarea value={form.schemaJson} onChange={(e) => patch("schemaJson", e.target.value)} rows={4} />
            </label>
          </>
        )}

        {step === 5 && (
          <>
            <h2>Probar conexión</h2>
            <p className="muted">Verifique conectividad y permisos antes de activar.</p>
            {testResult && (
              <div className={testResult.resultado === "EXITOSA" ? "alert alert-success" : "alert alert-error"}>
                {testResult.resultado}: {testResult.mensaje}
              </div>
            )}
          </>
        )}

        {step === 6 && (
          <>
            <h2>Activar</h2>
            <p>El conector quedará en estado <strong>Activo</strong> y podrá ejecutarse manualmente, por evento o vía automatizaciones.</p>
          </>
        )}

        <div className="toolbar" style={{ marginTop: "1.5rem" }}>
          <button type="button" className="btn" disabled={step === 0} onClick={() => setStep((s) => s - 1)}>
            Anterior
          </button>
          <button type="button" className="btn primary" onClick={() => void next()}>
            {step === STEPS.length - 1 ? "Activar conector" : "Siguiente"}
          </button>
        </div>
      </section>
    </div>
  );
}
