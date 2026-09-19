import type { DemoMeetingTopic } from "../lib/demoMeetingCatalog";
import type { DemoMetricSelection } from "./DemoExecutiveIntelligence";
import { getDemoPrivateMetricGuide } from "../lib/demoMetricPrivateCatalog";

type TraceRow={name:string;source:string;period:string;formula:string;records:string;filters:string};
const TRACE:Record<string,TraceRow[]>={
 facturacion:[{name:"Facturación / cartera",source:"Facturas demo + cartera",period:"Últimos 6 meses",formula:"Σ valores y saldos por pagador/servicio",records:"Facturas ficticias del paquete",filters:"Estado, pagador, servicio, fecha"}],
 glosas:[{name:"Pareto de glosas",source:"Glosas demo",period:"Últimos 6 meses",formula:"Frecuencia y valor causal / total",records:"Glosas y devoluciones ficticias",filters:"Causal, servicio, pagador"}],
 rrhh:[{name:"Capacidad y productividad",source:"Novedades y carga demo",period:"Mes demostrativo",formula:"Carga, horas y reproceso / capacidad",records:"Turnos y tareas ficticias",filters:"Área, rol, turno"}],
 operaciones:[{name:"Tiempo y reproceso",source:"Eventos de proceso demo",period:"Ciclo demostrativo",formula:"Tiempo entre etapas + retornos / casos",records:"Eventos ficticios por etapa",filters:"Etapa, responsable, resultado"}],
 compras:[{name:"Ahorro e inventario",source:"Compras + inventario demo",period:"Últimos 6 meses",formula:"Brecha precio/consumo + stock en riesgo",records:"Órdenes y movimientos ficticios",filters:"Proveedor, insumo, rotación"}],
 sistemas:[{name:"Riesgos e integraciones",source:"Inventario TI demo",period:"Corte demostrativo",formula:"Probabilidad × impacto + carga manual",records:"Aplicaciones, interfaces y riesgos ficticios",filters:"Criticidad, control, dependencia"}],
};
export function DemoTraceability({topic,metric}:{topic:DemoMeetingTopic;metric?:DemoMetricSelection|null}){
 const rows=TRACE[topic.id]??[]; const detail=metric?getDemoPrivateMetricGuide(metric.topicId,metric.title):null;
 return <section className="panel demo-trace"><div className="section-header"><div><span className="semantic-badge hecho">SIMULACIÓN</span><h2>Detalle y trazabilidad · {topic.label}</h2><p className="muted">Origen auditable del tema activo. En operación real se sustituye por fuentes y registros de la empresa.</p></div></div>
 {metric&&detail&&<aside className="trace-private-focus"><span>PRIVADO · SOLO PRESENTADOR · NO PUBLICADO</span><h3>{metric.title} · {metric.value}</h3><div className="trace-private-grid"><section><p><b>Lectura:</b> {metric.note}</p><p><b>Fuente:</b> {detail.source}</p><p><b>Período:</b> {detail.period}</p><p><b>Fórmula / regla:</b> {detail.formula}</p><p><b>Filtros:</b> {detail.filters}</p><p><b>Calidad:</b> {detail.quality}</p></section><section><b>Cómo intervenir / capturar valor</b><ol>{detail.strategy.map(x=><li key={x}>{x}</li>)}</ol><b>Respuesta ejecutiva sugerida</b><p>{detail.answer}</p></section></div><details><summary>Registros/evidencia que deben soportarlo</summary><p>{detail.records}</p><ul>{detail.realData.map(x=><li key={x}>{x}</li>)}</ul></details></aside>}
 {rows.map(r=><div className="trace-card" key={r.name}><h3>{r.name}</h3><div className="trace-grid"><div><small>Fuente / sistema</small><b>{r.source}</b></div><div><small>Período</small><b>{r.period}</b></div><div><small>Fórmula / regla</small><b>{r.formula}</b></div><div><small>Registros considerados</small><b>{r.records}</b></div><div><small>Filtros</small><b>{r.filters}</b></div><div><small>Fecha de cálculo</small><b>Generado para la demo actual</b></div></div><div className="trace-note">DEMO · Datos simulados. En operación real se podrá bajar hasta los registros que componen cada indicador.</div></div>)}
 </section>;
}
