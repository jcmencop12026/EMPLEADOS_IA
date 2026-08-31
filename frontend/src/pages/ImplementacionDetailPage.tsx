import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  aprobarImplGoLive,
  aprobarImplPiloto,
  calcularImplSalud,
  completarImplHito,
  createImplBloqueador,
  createImplEntregable,
  createImplExpansion,
  createImplExitoPlan,
  createImplHito,
  createImplPiloto,
  createImplRenovacion,
  createImplRequisito,
  evaluarImplReadiness,
  fetchContinuidadVistaPorProyecto,
  fetchImplEntregables,
  fetchImplProyectoDetalle,
  medirImplObjetivo,
  registrarImplAdopcion,
  registrarImplPilotoResultado,
  updateImplEntregable,
  type ContinuidadVista,
  type ImplEntregable,
  type ImplProyectoDetalle,
} from "../api";
import { ContinuidadVistaPanel } from "../components/continuidad/ContinuidadVistaPanel";
import { ImplementationCycleBar } from "../components/comercial/ImplementationCycleBar";
import { formatMoney } from "../lib/comercialLabels";
import { usePermissions } from "../hooks/usePermissions";

const CHECKLIST = [
  "configuracion", "usuarios", "permisos", "integraciones", "seguridad",
  "datos", "monitoreo", "soporte", "respaldo", "documentacion", "capacitacion",
];

export function ImplementacionDetailPage() {
  const { proyectoId } = useParams<{ proyectoId: string }>();
  const { has } = usePermissions();
  const [detalle, setDetalle] = useState<ImplProyectoDetalle | null>(null);
  const [tab, setTab] = useState("resumen");
  const [salud, setSalud] = useState<Record<string, unknown> | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [entregables, setEntregables] = useState<ImplEntregable[]>([]);
  const [vista, setVista] = useState<ContinuidadVista | null>(null);

  async function reload() {
    if (!proyectoId) return;
    setDetalle(await fetchImplProyectoDetalle(proyectoId));
    if (has("implementacion.view")) {
      fetchImplEntregables(proyectoId).then(setEntregables).catch(() => setEntregables([]));
    }
    if (has("continuidad_comercial.view")) {
      fetchContinuidadVistaPorProyecto(proyectoId).then(setVista).catch(() => setVista(null));
    }
  }

  useEffect(() => {
    reload();
  }, [proyectoId]);

  if (!detalle) return <p>Cargando…</p>;

  const t = detalle.tablero;

  async function onReadiness() {
    if (!proyectoId) return;
    const r = await evaluarImplReadiness(proyectoId, {
      DATOS: 0.9, TECNOLOGIA: 0.8, INTEGRACIONES: 0.7, PERSONAL: 0.9,
      GOBIERNO: 0.8, SEGURIDAD: 0.9, PROCESOS: 0.7, APROBACIONES: 0.8,
    });
    setMsg(`Readiness: ${r.resultado}`);
    reload();
  }

  async function onPilotoFlow() {
    if (!proyectoId) return;
    const pil = await createImplPiloto(proyectoId, { alcance: "Área prueba", duracion_dias: 30 });
    await registrarImplPilotoResultado(pil.id, { resultado: "EXITOSO", explicacion: "Métricas cumplidas" });
    await aprobarImplPiloto(pil.id, {});
    setMsg("Piloto aprobado para producción");
    reload();
  }

  async function onGoLive(e: FormEvent) {
    e.preventDefault();
    if (!proyectoId) return;
    const checklist = Object.fromEntries(CHECKLIST.map((k) => [k, true]));
    try {
      await aprobarImplGoLive(proyectoId, { checklist });
      setMsg("Go-live aprobado");
      reload();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "Error en go-live");
    }
  }

  return (
    <div className="ops-page">
      <header className="ops-header">
        <Link to="/implementacion">← Implementaciones</Link>
        <h1>{detalle.codigo} — {detalle.titulo}</h1>
        <p className="muted">Estado: {detalle.estado} · Avance: {detalle.avance_pct}%</p>
        <ImplementationCycleBar estado={detalle.estado} />
      </header>
      {msg && <p className="info-text">{msg}</p>}
      <nav className="tab-nav">
        {["resumen", "hitos", "entregables", "preparacion", "piloto", "adopcion", "exito", "renovacion", "continuidad", "salud"].map((x) => (
          <button key={x} type="button" className={tab === x ? "active" : ""} onClick={() => setTab(x)}>
            {x === "exito" ? "Éxito" : x === "renovacion" ? "Renovación" : x.charAt(0).toUpperCase() + x.slice(1)}
          </button>
        ))}
      </nav>
      {tab === "resumen" && t && (
        <section className="panel compact-panel">
          <h2>Seguimiento del valor</h2>
          <div className="metrics-grid compact-metrics">
            <div><strong>Fase actual</strong><span>{t.fase_actual}</span></div>
            <div><strong>Valor comprometido</strong><span>{formatMoney(detalle.valor_compromiso?.valor_atribuible_total as number | undefined)}</span></div>
            <div><strong>Precio comprometido</strong><span>{formatMoney((detalle.valor_compromiso?.precio_final ?? detalle.valor_compromiso?.precio_sugerido) as number | undefined)}</span></div>
            {t.tco && <div><strong>TCO integrado</strong><span>{formatMoney(t.tco.total)}</span></div>}
            {t.salud && <div><strong>Salud cliente</strong><span>{t.salud.resultado} ({t.salud.puntuacion})</span></div>}
          </div>
          {t.trazabilidad && (
            <details className="compact-details">
              <summary>Trazabilidad implementación</summary>
              <ul className="compact-list">
                <li>Qué vendimos: {JSON.stringify(t.trazabilidad.que_vendimos)}</li>
                <li>Qué prometimos: {String(t.trazabilidad.que_prometimos ?? "—")}</li>
                <li>Qué implementamos: {String(t.trazabilidad.que_implementamos ?? "—")}</li>
              </ul>
            </details>
          )}
          {detalle.proposal_id && (
            <p>
              <Link to={`/centro-negocios/propuestas/${detalle.proposal_id}`}>Ver expediente Centro de Negocios →</Link>
            </p>
          )}
        </section>
      )}
      {tab === "entregables" && (
        <section className="panel">
          <h2>Entregables formales</h2>
          {entregables.length === 0 ? (
            <p className="muted">Sin entregables registrados.</p>
          ) : (
            <table className="data-table compact-table">
              <thead><tr><th>Nombre</th><th>Estado</th><th>Aceptación</th><th>Evidencia</th></tr></thead>
              <tbody>
                {entregables.map((e) => (
                  <tr key={e.id}>
                    <td>{e.nombre}</td>
                    <td>{e.estado}</td>
                    <td>{e.aceptacion ?? "—"}</td>
                    <td>{e.evidencia ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {has("implementacion.manage") && proyectoId && (
            <button
              type="button"
              onClick={async () => {
                const nombre = window.prompt("Nombre del entregable:");
                if (!nombre) return;
                const ent = await createImplEntregable(proyectoId, { nombre, descripcion: "Entrega formal" });
                await updateImplEntregable(ent.id, { aceptacion: "PENDIENTE" });
                setMsg(`Entregable creado: ${ent.nombre}`);
                reload();
              }}
            >
              Registrar entregable
            </button>
          )}
        </section>
      )}
      {tab === "hitos" && (
        <section className="panel">
          <h2>Hitos y tareas</h2>
          <ul>{detalle.hitos?.map((h) => <li key={h.id}>{h.nombre} — {h.estado}</li>)}</ul>
          {has("implementacion.manage") && proyectoId && (
            <button type="button" onClick={async () => {
              const h = await createImplHito(proyectoId, { nombre: "Diagnóstico aprobado" });
              await completarImplHito(h.id, { evidencia: "OK" });
              reload();
            }}>Agregar y completar hito</button>
          )}
        </section>
      )}
      {tab === "preparacion" && has("implementacion.manage") && (
        <section className="panel">
          <h2>Preparación</h2>
          <button type="button" onClick={onReadiness}>Evaluar readiness</button>
          <button type="button" onClick={async () => {
            if (!proyectoId) return;
            await createImplRequisito(proyectoId, { tipo: "ACCESOS", descripcion: "VPN cliente", bloqueante: false });
            reload();
          }}>Agregar requisito</button>
        </section>
      )}
      {tab === "piloto" && has("implementacion.manage") && (
        <section className="panel">
          <h2>Piloto</h2>
          <button type="button" onClick={onPilotoFlow}>Flujo piloto completo</button>
          {has("implementacion.approve_go_live") && (
            <form onSubmit={onGoLive}>
              <h3>Go-live</h3>
              <button type="submit">Aprobar salida a producción</button>
            </form>
          )}
        </section>
      )}
      {tab === "adopcion" && (
        <section className="panel">
          <h2>Adopción</h2>
          <button type="button" onClick={async () => {
            if (!proyectoId) return;
            await registrarImplAdopcion(proyectoId, { metricas: { usuarios_habilitados: 50, usuarios_activos: 40 } });
            reload();
          }}>Registrar adopción</button>
        </section>
      )}
      {tab === "exito" && (
        <section className="panel">
          <h2>Éxito del cliente</h2>
          <button type="button" onClick={async () => {
            if (!proyectoId) return;
            const plan = await createImplExitoPlan({ proyecto_id: proyectoId, titulo: "Plan éxito", valor_esperado: 10000000 });
            setMsg(`Plan creado: ${plan.id}`);
          }}>Crear plan de éxito</button>
        </section>
      )}
      {tab === "renovacion" && has("exito_cliente.manage") && (
        <section className="panel">
          <h2>Renovación y ampliación</h2>
          <p className="muted">Detecte oportunidades de renovación o expansión sin duplicar el CRM.</p>
          <button
            type="button"
            onClick={async () => {
              if (!proyectoId) return;
              const res = await createImplRenovacion({
                proyecto_id: proyectoId,
                notas: "Renovación próxima",
                crear_oportunidad: true,
                titulo_oportunidad: "Renovación contrato",
              });
              setMsg(res.opportunity_id ? `Oportunidad creada: ${res.opportunity_id}` : "Renovación registrada");
            }}
          >
            Registrar renovación y crear oportunidad
          </button>
          <button
            type="button"
            onClick={async () => {
              if (!proyectoId) return;
              const res = await createImplExpansion({
                proyecto_id: proyectoId,
                tipo: "NUEVO_PROCESO",
                descripcion: "Ampliación de alcance",
                crear_oportunidad: true,
                titulo_oportunidad: "Expansión capacidad",
              });
              setMsg(res.opportunity_id ? `Oportunidad expansión: ${res.opportunity_id}` : "Expansión registrada");
            }}
          >
            Registrar ampliación
          </button>
        </section>
      )}
      {tab === "continuidad" && has("continuidad_comercial.view") && (
        <ContinuidadVistaPanel vista={vista} canManage={false} canClose={false} />
      )}
      {tab === "salud" && (
        <section className="panel">
          <h2>Salud del cliente</h2>
          <button type="button" onClick={async () => {
            if (!proyectoId) return;
            setSalud(await calcularImplSalud(proyectoId));
          }}>Calcular salud</button>
          {salud && <pre>{JSON.stringify(salud, null, 2)}</pre>}
        </section>
      )}
    </div>
  );
}
