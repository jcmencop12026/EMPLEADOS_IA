import { FormEvent, useEffect, useMemo, useState } from "react";
import type { CommChannel, CommMessage, CommRule, CommTemplate } from "../api";
import {
  cancelCommMessage,
  createCommChannel,
  createCommMessage,
  createCommRule,
  createCommTemplate,
  createCommTemplateVersion,
  fetchCommCentroResumen,
  fetchCommChannels,
  fetchCommMessage,
  fetchCommMessages,
  fetchCommPreferences,
  fetchCommRules,
  fetchCommTemplates,
  updateCommPreferences,
} from "../api";
import { ContextualHelp } from "../components/ContextualHelp";
import { EiaaxTable, type EiaaxColumn } from "../components/EiaaxTable";
import { HELP_CENTRO_INFORMACION } from "../lib/comunicacionesHelp";

type Tab = "bandeja" | "plantillas" | "reglas" | "canales" | "programadas" | "historial" | "preferencias";

const ESTADO_LABELS: Record<string, string> = {
  BORRADOR: "Borrador",
  PROGRAMADA: "Programada",
  PENDIENTE_ENVIO: "Pendiente de envío",
  ENVIANDO: "Enviando",
  ENVIADA: "Enviada",
  ENTREGADA: "Entregada",
  FALLIDA: "Fallida",
  CANCELADA: "Cancelada",
};

export function ComunicacionesPage() {
  const [tab, setTab] = useState<Tab>("bandeja");
  const [channels, setChannels] = useState<CommChannel[]>([]);
  const [templates, setTemplates] = useState<CommTemplate[]>([]);
  const [rules, setRules] = useState<CommRule[]>([]);
  const [messages, setMessages] = useState<CommMessage[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<CommMessage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filterEstado, setFilterEstado] = useState("");
  const [filterQ, setFilterQ] = useState("");
  const [showNew, setShowNew] = useState(false);
  const [resumen, setResumen] = useState<Record<string, number> | null>(null);
  const [prefs, setPrefs] = useState({ canales: [] as string[], tipos: [] as string[], idioma: "es" });

  const [newTpl, setNewTpl] = useState({
    codigo: "",
    nombre: "",
    tipo_comunicacion: "OPERATIVA",
    canal_tipo: "INTERNO_PLATAFORMA",
    asunto: "",
    contenido: "Hola {{nombre}}, mensaje de {{empresa}} el {{fecha}}.",
  });
  const [newRule, setNewRule] = useState({
    nombre: "",
    event_type: "SUPPORT_SLA_RISK",
    destinatario_tipo: "DINAMICO",
    destinatario_regla: "RESPONSABLE_CASO",
    condicion: '{"match":{"prioridad":"alta"}}',
  });
  const [newMsg, setNewMsg] = useState({
    channel_id: "",
    template_version_id: "",
    destinatario_tipo: "USUARIO",
    destinatario_id: "",
    programada_para: "",
    enviar_ahora: true,
  });

  const reload = async () => {
    try {
      const [ch, tpl, rl, msg] = await Promise.all([
        fetchCommChannels(),
        fetchCommTemplates(),
        fetchCommRules(),
        fetchCommMessages(tab === "programadas" ? "programadas=true" : ""),
      ]);
      setChannels(ch);
      setTemplates(tpl);
      setRules(rl);
      setMessages(msg);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar comunicaciones");
    }
  };

  useEffect(() => {
    reload();
    fetchCommCentroResumen().then(setResumen).catch(() => undefined);
    if (tab === "preferencias") {
      fetchCommPreferences().then((p) =>
        setPrefs({ canales: p.canales ?? [], tipos: p.tipos ?? [], idioma: p.idioma ?? "es" }),
      );
    }
  }, [tab]);

  useEffect(() => {
    if (!selectedId) {
      setDetail(null);
      return;
    }
    fetchCommMessage(selectedId)
      .then(setDetail)
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar detalle"));
  }, [selectedId]);

  const filtered = useMemo(() => {
    return messages.filter((m) => {
      if (filterEstado && m.estado !== filterEstado) return false;
      if (filterQ) {
        const hay = `${m.asunto ?? ""} ${m.contenido ?? ""}`.toLowerCase();
        if (!hay.includes(filterQ.toLowerCase())) return false;
      }
      if (tab === "programadas" && m.estado !== "PROGRAMADA") return false;
      if (tab === "historial" && !["ENVIADA", "FALLIDA", "CANCELADA", "ENTREGADA"].includes(m.estado)) return false;
      return true;
    });
  }, [messages, filterEstado, filterQ, tab]);

  const onCreateTemplate = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await createCommTemplate(newTpl);
      setNewTpl({ ...newTpl, codigo: "", nombre: "", asunto: "" });
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo crear la plantilla");
    }
  };

  const onVersionTemplate = async (templateId: string) => {
    const contenido = window.prompt("Nuevo contenido de plantilla:", "Actualización: {{nombre}} — {{fecha}}");
    if (!contenido) return;
    try {
      await createCommTemplateVersion(templateId, { contenido, asunto: "Aviso actualizado" });
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo versionar");
    }
  };

  const onCreateRule = async (e: FormEvent) => {
    e.preventDefault();
    const tpl = templates[0];
    const ch = channels.find((c) => c.tipo === (tpl?.canal_tipo ?? "INTERNO_PLATAFORMA")) ?? channels[0];
    if (!tpl?.current_version_id || !ch) {
      setError("Cree al menos una plantilla y un canal antes de la regla.");
      return;
    }
    try {
      await createCommRule({
        ...newRule,
        template_version_id: tpl.current_version_id,
        channel_id: ch.id,
        condicion: JSON.parse(newRule.condicion),
      });
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo crear la regla");
    }
  };

  const onCreateChannel = async () => {
    const nombre = window.prompt("Nombre del canal interno:", "Bandeja interna");
    if (!nombre) return;
    try {
      await createCommChannel({ tipo: "INTERNO_PLATAFORMA", nombre });
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo crear el canal");
    }
  };

  const onSendMessage = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await createCommMessage({
        channel_id: newMsg.channel_id,
        template_version_id: newMsg.template_version_id || undefined,
        destinatario_tipo: newMsg.destinatario_tipo,
        destinatario_id: newMsg.destinatario_id || undefined,
        programada_para: newMsg.programada_para || undefined,
        enviar_ahora: newMsg.enviar_ahora,
        tipo_comunicacion: "MANUAL",
      });
      setShowNew(false);
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo enviar");
    }
  };

  const messageColumns = useMemo<EiaaxColumn<CommMessage>[]>(
    () => [
      {
        key: "created_at",
        label: "Fecha",
        getValue: (m) => m.created_at,
        render: (m) => (m.created_at ? new Date(m.created_at).toLocaleString("es-CO") : "—"),
      },
      { key: "tipo_comunicacion", label: "Tipo", sortable: true, getValue: (m) => m.tipo_comunicacion },
      {
        key: "destinatario",
        label: "Destinatario",
        render: (m) => m.destinatario_id || m.destinatario_externo || m.destinatario_tipo,
      },
      { key: "channel_tipo", label: "Canal", getValue: (m) => m.channel_tipo },
      { key: "asunto", label: "Asunto", sortable: true, getValue: (m) => m.asunto },
      {
        key: "estado",
        label: "Estado",
        sortable: true,
        getValue: (m) => m.estado,
        render: (m) => ESTADO_LABELS[m.estado] ?? m.estado,
      },
      { key: "origen", label: "Origen", getValue: (m) => m.origen },
      {
        key: "acciones",
        label: "",
        render: (m) => (
          <>
            <button type="button" className="btn link" onClick={() => setSelectedId(m.id)}>
              Ver
            </button>
            {m.estado === "PROGRAMADA" && (
              <button type="button" className="btn link" onClick={() => cancelCommMessage(m.id).then(reload)}>
                Cancelar
              </button>
            )}
          </>
        ),
      },
    ],
    [],
  );

  const tabs: { id: Tab; label: string }[] = [
    { id: "bandeja", label: "Bandeja" },
    { id: "plantillas", label: "Plantillas" },
    { id: "reglas", label: "Reglas" },
    { id: "canales", label: "Canales" },
    { id: "programadas", label: "Programadas" },
    { id: "historial", label: "Historial" },
    { id: "preferencias", label: "Preferencias" },
  ];

  return (
    <div className="page comunicaciones-page ops-page">
      <header className="page-header">
        <div className="page-header-row">
          <div>
            <h1>Centro de Información y Comunicaciones</h1>
            <p className="muted">
              Comunicaciones gobernadas, entrega de informes y trazabilidad — complementa notificaciones (820).
            </p>
          </div>
          <ContextualHelp content={HELP_CENTRO_INFORMACION} />
        </div>
        <button type="button" className="btn primary" onClick={() => setShowNew(true)}>
          Nueva comunicación
        </button>
      </header>

      {resumen && (
        <div className="eval-metrics metrics-grid compact">
          <div className="metric-card">
            <span className="metric-label">Pendientes</span>
            <strong>{resumen.pendientes}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Fallidas</span>
            <strong>{resumen.comunicaciones_fallidas ?? resumen.fallidas}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Informes entregados</span>
            <strong>{resumen.informes_entregados}</strong>
          </div>
          <div className="metric-card">
            <span className="metric-label">Programadas</span>
            <strong>{resumen.programadas}</strong>
          </div>
        </div>
      )}

      {error && <div className="alert alert-error">{error}</div>}

      <nav className="tab-row" style={{ marginBottom: "1rem" }}>
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            className={tab === t.id ? "btn primary" : "btn"}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {(tab === "bandeja" || tab === "programadas" || tab === "historial") && (
        <section className="panel compact-panel">
          <EiaaxTable
            columns={messageColumns}
            data={filtered}
            rowKey={(m) => m.id}
            prefsKey={`comms_${tab}_v1`}
            searchPlaceholder="Buscar asunto o contenido…"
            searchKeys={["asunto", "contenido", "tipo_comunicacion"]}
            emptyMessage="Sin comunicaciones en esta vista."
            defaultSortKey="created_at"
          />
          {detail && selectedId && (
            <div className="card" style={{ marginTop: "1rem" }}>
              <h3>Detalle de comunicación</h3>
              <p><strong>Evento:</strong> {detail.event_id ?? "—"}</p>
              <p><strong>ID de correlación:</strong> {detail.correlation_id ?? "—"}</p>
              <p><strong>Plantilla v:</strong> {detail.template_version ?? "—"}</p>
              <p><strong>Regla:</strong> {detail.rule_id ?? "—"}</p>
              <p><strong>Contenido:</strong> {detail.contenido}</p>
              {detail.historial_intentos && detail.historial_intentos.length > 0 && (
                <ul>
                  {detail.historial_intentos.map((h, i) => (
                    <li key={i}>{String(h.fecha)} — {String(h.estado)} — {String(h.detalle ?? "")}</li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </section>
      )}

      {tab === "preferencias" && (
        <section className="panel compact-panel">
          <h2>Preferencias de comunicación</h2>
          <form
            className="form-grid"
            onSubmit={async (e) => {
              e.preventDefault();
              try {
                await updateCommPreferences(prefs);
                setError(null);
              } catch (err) {
                setError(err instanceof Error ? err.message : "No se guardaron preferencias");
              }
            }}
          >
            <label>
              Canales permitidos (separados por coma)
              <input
                value={prefs.canales.join(", ")}
                onChange={(e) =>
                  setPrefs({ ...prefs, canales: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) })
                }
              />
            </label>
            <label>
              Tipos silenciados (no críticos)
              <input
                value={prefs.tipos.join(", ")}
                onChange={(e) =>
                  setPrefs({ ...prefs, tipos: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) })
                }
              />
            </label>
            <label>
              Idioma
              <select value={prefs.idioma} onChange={(e) => setPrefs({ ...prefs, idioma: e.target.value })}>
                <option value="es">Español</option>
              </select>
            </label>
            <button type="submit" className="btn primary">
              Guardar preferencias
            </button>
          </form>
          <p className="muted small">Las alertas obligatorias de política empresarial no pueden silenciarse.</p>
        </section>
      )}

      {tab === "plantillas" && (
        <section className="card">
          <h2>Plantillas</h2>
          <form onSubmit={onCreateTemplate} className="form-grid" style={{ marginBottom: "1.5rem" }}>
            <input placeholder="Código" value={newTpl.codigo} onChange={(e) => setNewTpl({ ...newTpl, codigo: e.target.value })} required />
            <input placeholder="Nombre" value={newTpl.nombre} onChange={(e) => setNewTpl({ ...newTpl, nombre: e.target.value })} required />
            <input placeholder="Asunto" value={newTpl.asunto} onChange={(e) => setNewTpl({ ...newTpl, asunto: e.target.value })} />
            <textarea placeholder="Contenido" value={newTpl.contenido} onChange={(e) => setNewTpl({ ...newTpl, contenido: e.target.value })} required />
            <button type="submit" className="btn primary">Crear plantilla</button>
          </form>
          <table className="data-table">
            <thead>
              <tr>
                <th>Código</th>
                <th>Nombre</th>
                <th>Canal</th>
                <th>Versión</th>
                <th>Idioma</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {templates.map((t) => (
                <tr key={t.id}>
                  <td>{t.codigo}</td>
                  <td>{t.nombre}</td>
                  <td>{t.canal_tipo}</td>
                  <td>v{t.current_version}</td>
                  <td>{t.idioma}</td>
                  <td>
                    <button type="button" className="btn link" onClick={() => onVersionTemplate(t.id)}>
                      Nueva versión
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {tab === "reglas" && (
        <section className="card">
          <h2>Reglas de comunicación</h2>
          <form onSubmit={onCreateRule} className="form-grid" style={{ marginBottom: "1.5rem" }}>
            <input placeholder="Nombre" value={newRule.nombre} onChange={(e) => setNewRule({ ...newRule, nombre: e.target.value })} required />
            <input placeholder="Tipo de evento" value={newRule.event_type} onChange={(e) => setNewRule({ ...newRule, event_type: e.target.value })} required />
            <input placeholder="Condición JSON" value={newRule.condicion} onChange={(e) => setNewRule({ ...newRule, condicion: e.target.value })} />
            <button type="submit" className="btn primary">Crear regla</button>
          </form>
          <table className="data-table">
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Evento</th>
                <th>Destinatario</th>
                <th>Acción</th>
                <th>Activa</th>
              </tr>
            </thead>
            <tbody>
              {rules.map((r) => (
                <tr key={r.id}>
                  <td>{r.nombre}</td>
                  <td>{r.event_type}</td>
                  <td>{r.destinatario_tipo} / {r.destinatario_regla}</td>
                  <td>{r.accion}</td>
                  <td>{r.activo ? "Sí" : "No"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {tab === "canales" && (
        <section className="card">
          <div className="toolbar" style={{ marginBottom: "1rem" }}>
            <h2>Canales</h2>
            <button type="button" className="btn" onClick={onCreateChannel}>Añadir canal interno</button>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Tipo</th>
                <th>Estado</th>
                <th>Activo</th>
                <th>Secreto</th>
                <th>Prioridad</th>
              </tr>
            </thead>
            <tbody>
              {channels.map((c) => (
                <tr key={c.id}>
                  <td>{c.nombre}</td>
                  <td>{c.tipo}</td>
                  <td>{c.estado}</td>
                  <td>{c.activo ? "Sí" : "No"}</td>
                  <td>{c.secret_configured ? "Configurado" : "No"}</td>
                  <td>{c.prioridad}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {showNew && (
        <div className="modal-backdrop" role="dialog" aria-modal="true">
          <div className="card modal">
            <h2>Nueva comunicación</h2>
            <form onSubmit={onSendMessage} className="form-grid">
              <label>
                Canal
                <select value={newMsg.channel_id} onChange={(e) => setNewMsg({ ...newMsg, channel_id: e.target.value })} required>
                  <option value="">Seleccionar</option>
                  {channels.map((c) => (
                    <option key={c.id} value={c.id}>{c.nombre} ({c.tipo})</option>
                  ))}
                </select>
              </label>
              <label>
                Plantilla (opcional)
                <select value={newMsg.template_version_id} onChange={(e) => setNewMsg({ ...newMsg, template_version_id: e.target.value })}>
                  <option value="">Sin plantilla</option>
                  {templates.map((t) => (
                    <option key={t.id} value={t.current_version_id ?? ""}>{t.codigo} v{t.current_version}</option>
                  ))}
                </select>
              </label>
              <label>
                Destinatario (usuario)
                <input value={newMsg.destinatario_id} onChange={(e) => setNewMsg({ ...newMsg, destinatario_id: e.target.value })} />
              </label>
              <label>
                Programar (ISO)
                <input type="datetime-local" value={newMsg.programada_para} onChange={(e) => setNewMsg({ ...newMsg, programada_para: e.target.value, enviar_ahora: !e.target.value })} />
              </label>
              <div className="toolbar">
                <button type="button" className="btn" onClick={() => setShowNew(false)}>Cerrar</button>
                <button type="submit" className="btn primary">Enviar / programar</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
