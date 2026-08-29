import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  aprobarImplGoLive,
  aprobarImplPiloto,
  calcularImplSalud,
  completarImplHito,
  createImplBloqueador,
  createImplExitoPlan,
  createImplHito,
  createImplPiloto,
  createImplRequisito,
  evaluarImplReadiness,
  fetchImplProyectoDetalle,
  medirImplObjetivo,
  registrarImplAdopcion,
  registrarImplPilotoResultado,
  type ImplProyectoDetalle,
} from "../api";
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

  async function reload() {
    if (!proyectoId) return;
    setDetalle(await fetchImplProyectoDetalle(proyectoId));
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
        <p>Estado: {detalle.estado} | Avance: {detalle.avance_pct}%</p>
      </header>
      {msg && <p className="info-text">{msg}</p>}
      <nav className="tab-nav">
        {["resumen", "hitos", "preparacion", "piloto", "adopcion", "exito", "salud"].map((x) => (
          <button key={x} type="button" className={tab === x ? "active" : ""} onClick={() => setTab(x)}>
            {x.charAt(0).toUpperCase() + x.slice(1)}
          </button>
        ))}
      </nav>
      {tab === "resumen" && t && (
        <section className="panel">
          <h2>Tablero</h2>
          <p>Fase actual: {t.fase_actual}</p>
          <p>Valor comprometido: {JSON.stringify(t.valor_esperado)}</p>
          {t.tco && <p>TCO integrado: {t.tco.total}</p>}
          <pre>{JSON.stringify(t.trazabilidad, null, 2)}</pre>
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
