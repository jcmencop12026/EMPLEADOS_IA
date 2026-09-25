import { useEffect, useMemo, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { fetchDemoSalaPublic, sendDemoGuestInterest, type DemoSala } from "../api";
import { DEMO_MEETING_TOPICS } from "../lib/demoMeetingCatalog";
import { DemoDomainVisuals } from "../components/DemoDomainVisuals";

const IMPACTS=[["↗","Ingresos"],["↘","Pérdidas"],["◉","Costos"],["⚡","Productividad"],["◇","Riesgos"]] as const;
const IMPACT_DETAIL:any={Ingresos:{value:"+$185 M",title:"Nuevos ingresos",text:"Capacidad disponible y demanda no capturada."},"Pérdidas":{value:"$128 M",title:"Caja recuperable",text:"Segmento priorizado dentro de la cartera bajo análisis."},Costos:{value:"$54 M",title:"Costos evitables",text:"Reprocesos y actividades con oportunidad de eficiencia."},Productividad:{value:"18,7 días",title:"Ciclo factura → radicación",text:"Reducir tiempos acelera el ingreso y libera capacidad."},Riesgos:{value:"$742 M",title:"Cartera >90 días",text:"Exposición que requiere segmentación y gestión."}};
const EXECUTIVE_OPPORTUNITIES=[
 {icon:"↗",value:"+$185 M",title:"Capacidad disponible que podría convertirse en nuevos ingresos",priority:"ALTA",impact:"Ingresos"},
 {icon:"💰",value:"+$128 M",title:"Cartera para intervención prioritaria",priority:"ALTA",impact:"Pérdidas"},
 {icon:"⏱",value:"$96 M",title:"Facturación cuyo ciclo puede acelerarse",priority:"ALTA",impact:"Productividad"},
 {icon:"◉",value:"$54 M",title:"Costos y reprocesos bajo análisis",priority:"MEDIA",impact:"Costos"},
 {icon:"⚠",value:"$742 M",title:"Cartera mayor a 90 días bajo observación",priority:"RIESGO",impact:"Riesgos"},
 {icon:"⚡",value:"18,7 días",title:"Ciclo factura → radicación por optimizar",priority:"PROCESO",impact:"Productividad"}
] as const;
export function DemoGuestRoomPage(){
 const {codigo=""}=useParams(); const [sp]=useSearchParams(); const token=sp.get("token")||"";
 const [sala,setSala]=useState<DemoSala|null>(null),[error,setError]=useState<string|null>(null),[interestMsg,setInterestMsg]=useState<string|null>(null),[guestQuestion,setGuestQuestion]=useState("");
 const [impact,setImpact]=useState("Ingresos"),[panel,setPanel]=useState<"hallazgo"|"evidencia"|"importa"|"accion"|"avance">("hallazgo"),[focus,setFocus]=useState(0);
 useEffect(()=>{let stop=false;const load=()=>fetchDemoSalaPublic(codigo,token).then(x=>{if(!stop){setSala(x);setError(null)}}).catch(e=>{if(!stop)setError(e.message)});load();const id=setInterval(load,1500);return()=>{stop=true;clearInterval(id)}},[codigo,token]);
 const v=sala?.visible as any; const topic=useMemo(()=>DEMO_MEETING_TOPICS.find(t=>t.id===sala?.tema)||DEMO_MEETING_TOPICS[0],[sala?.tema]); const findings=Array.isArray(v?.contenido)&&v.contenido.length?v.contenido:topic.hallazgos;
 const topicMetrics=topic.indicadores.slice(0,4);
 const topicRadar=(topic.oportunidades.length?topic.oportunidades:topic.hallazgos).slice(0,6).map((title,i)=>({icon:["↗","💰","⏱","◉","⚠","⚡"][i]||"◆",value:topic.indicadores[i%Math.max(topic.indicadores.length,1)]||["+$185 M","$128 M","$96 M","$54 M","$742 M","18,7 días"][i],title:String(title).replace(/^Oportunidad:\s*/,""),priority:i<2?"ALTA":i<4?"MEDIA":"EXPLORAR"}));
 const registrar=async(accion:string,detalle:string)=>{try{await sendDemoGuestInterest(codigo,token,accion,topic.label,detalle);setInterestMsg(accion==="PREGUNTA_AUDIENCIA"?"✓ Pregunta enviada al presentador":"✓ Interés enviado al presentador");setTimeout(()=>setInterestMsg(null),3000)}catch{setInterestMsg("No fue posible enviar la interacción")}};
 const enviarPregunta=async(e:React.FormEvent)=>{e.preventDefault();const q=guestQuestion.trim();if(!q)return;await registrar("PREGUNTA_AUDIENCIA",q);setGuestQuestion("")};
 if(error&&!sala)return <main className="guest-room"><h1>EIIAX · Sala ejecutiva</h1><p className="error">{error}</p></main>;
 if(!sala)return <main className="guest-room"><h1>EIIAX · Sala ejecutiva</h1><p>Conectando con la reunión…</p></main>;
 const current=findings[Math.min(focus,findings.length-1)]||topic.oportunidades[0];
 const narrative=topic.narrativa[focus%topic.narrativa.length];
 const selectedRadar=topicRadar[Math.min(focus,Math.max(topicRadar.length-1,0))];
 const openFinding=(i:number)=>{setFocus(i);setPanel("hallazgo")};
 const selectImpact=(label:string)=>{setImpact(label);const i=EXECUTIVE_OPPORTUNITIES.findIndex(o=>o.impact===label);if(i>=0)setFocus(i);setPanel("hallazgo")};
 return <main className="guest-room guest-room-v8">
  {error&&<div className="info-box" role="status">Conexión temporalmente inestable. Se conserva la última vista y se reintenta automáticamente.</div>}
  <header className="guest-executive-header">
   <div className="guest-logo-plate"><img src="/assets/identity/eiaax-logo-approved.png" alt="EIIAX"/></div>
   <div className="guest-executive-title"><span className="semantic-badge hecho">● EN VIVO · {v?.nivel||"DEMO"}</span><h1>{v?.titulo||topic.label}</h1><p>IA aplicada para convertir evidencia en decisiones con impacto.</p></div>
   <div className="guest-impact guest-impact-top">{IMPACTS.map(([i,l])=><button key={l} className={impact===l?"active":""} onClick={()=>selectImpact(l)}><b>{i}</b>{l}</button>)}</div>
  </header>
  <section className="guest-v17-summary">
   <div><span>DEMO · DATOS SIMULADOS</span><strong>$463 M</strong><p>Potencial económico identificado</p><small>4 oportunidades económicas · $742 M de cartera bajo análisis</small></div>
   <div className="guest-v17-kpis">{topicMetrics.map((metric,i)=><button key={metric} onClick={()=>{setFocus(i);setPanel("evidencia")}}><b>{["↗","💰","⏱","◉"][i]}</b><strong>{metric}</strong><span>{["Señal principal","Valor / resultado","Tiempo / desempeño","Concentración / control"][i]}</span></button>)}</div>
  </section>
  <nav className="guest-actionbar guest-actionbar-v8 guest-actionbar-v15"><button className={panel==="hallazgo"?"active":""} onClick={()=>setPanel("hallazgo")}>◈ <span>Oportunidades</span></button><button className={panel==="evidencia"?"active":""} onClick={()=>setPanel("evidencia")}>▥ <span>Evidencia</span></button><button className={panel==="importa"?"active":""} onClick={()=>setPanel("importa")}>◎ <span>Impacto</span></button><button className={panel==="accion"?"active":""} onClick={()=>setPanel("accion")}>✓ <span>Qué haríamos</span></button><button className={panel==="avance"?"active":""} onClick={()=>setPanel("avance")}>↗ <span>Avances</span></button>{v?.respuesta&&<button className="guest-live-share" onClick={()=>document.getElementById("guest-presenter-share")?.scrollIntoView({behavior:"smooth",block:"center"})}>✦ <span>Desde la reunión</span><b>NUEVO</b></button>}</nav>
  <section className="guest-workspace guest-workspace-v8">
   {panel==="hallazgo"&&<div className="guest-v17-layout">
    <article className="guest-v17-focus">
     <header><span>{selectedRadar?.icon||"◈"} OPORTUNIDAD {String(focus+1).padStart(2,"0")}</span><b>{selectedRadar?.priority||"OPORTUNIDAD"}</b></header>
     <strong className="guest-v17-money">{selectedRadar?.value||topic.indicadores[0]||IMPACT_DETAIL[impact].value}</strong>
     <h2>{selectedRadar?.title||String(current).replace(/^Oportunidad:\s*/,"")}</h2>
     <p>{narrative}</p>
     <div className="guest-v17-facts"><span><b>23</b> servicios analizados</span><span><b>8</b> prioritarios</span><span><b>28%</b> capacidad disponible</span></div>
     <div className="guest-v17-tools"><button onClick={()=>setPanel("evidencia")}>▥ Evidencia</button><button onClick={()=>setPanel("importa")}>◎ Impacto</button><button onClick={()=>setPanel("accion")}>✓ Qué haríamos</button><button onClick={()=>setPanel("avance")}>↗ Seguimiento</button></div>
     <div className="guest-v17-data"><span>PARA VALIDARLO CON SUS DATOS</span><p>Facturación · RIPS/Producción · Cartera · Contratos · Capacidad instalada</p></div>
    </article>
    <aside className="guest-v17-radar"><header><div><span>RADAR DE OPORTUNIDADES</span><strong>Señales que merecen atención gerencial</strong></div><small>clic para profundizar</small></header>
     <div>{topicRadar.map((o,i)=><button key={o.title} className={focus===i?"active":""} onClick={()=>openFinding(i)}><b>{o.icon}</b><strong>{o.value}</strong><span>{o.title}</span><em>{o.priority}</em></button>)}</div>
    </aside>
   </div>}
   {panel==="evidencia"&&<div className="guest-v18-evidence"><header><span>▥ EVIDENCIA ECONÓMICA · {selectedRadar?.title||topic.label}</span><strong>Valores que sostienen la señal y permiten decidir dónde profundizar.</strong></header><div className="guest-v18-money-grid">{topic.indicadores.slice(0,6).map((metric,i)=><button key={metric} onClick={()=>setFocus(i%Math.max(topicRadar.length,1))}><b>{["↗","💰","⏱","◉","⚠","⚡"][i]}</b><strong>{metric}</strong><span>{topic.hallazgos[i%topic.hallazgos.length]}</span></button>)}</div><div className="guest-v18-evidence-detail"><DemoDomainVisuals topic={topic}/></div></div>}
   {panel==="importa"&&<div className="guest-v18-impact"><header><span>◎ IMPACTO · {IMPACT_DETAIL[impact].title}</span><strong>{IMPACT_DETAIL[impact].value}</strong><p>{IMPACT_DETAIL[impact].text}</p></header><div><button onClick={()=>setPanel("evidencia")}><b>💲</b><strong>Impacto económico</strong><span>{selectedRadar?.value||topic.indicadores[0]} asociado a la señal seleccionada.</span></button><button onClick={()=>setPanel("evidencia")}><b>▥</b><strong>Causa y evidencia</strong><span>Validar la magnitud con datos de la entidad.</span></button><button onClick={()=>setPanel("accion")}><b>✓</b><strong>Decisión sugerida</strong><span>Priorizar, validar y convertir la señal en un plan medible.</span></button><button onClick={()=>setPanel("avance")}><b>↗</b><strong>Cómo medirlo</strong><span>Línea base, meta, resultado y beneficio realizado.</span></button></div></div>}
   {panel==="avance"&&<div className="guest-progress-v9"><div className="guest-progress-head"><span>SEGUIMIENTO EJECUTIVO</span><h2>De la oportunidad identificada al beneficio realizado</h2><p>Esta vista se habilita con datos reales durante la implementación. En demo muestra la estructura de seguimiento, no resultados reales.</p></div><div className="guest-progress-kpis"><article><small>Avance de implementación</small><b>—</b><span>Pendiente de contratación</span></article><article><small>Potencial identificado</small><b>{IMPACT_DETAIL[impact].value}</b><span>Estimación demostrativa</span></article><article><small>Beneficio validado</small><b>—</b><span>Requiere línea base real</span></article><article><small>Beneficio realizado</small><b>—</b><span>Se acumula con evidencia</span></article></div><div className="guest-progress-flow"><div><b>1</b><strong>Línea base</strong><span>Validar punto de partida</span></div><div><b>2</b><strong>Plan e hitos</strong><span>Responsables y fechas</span></div><div><b>3</b><strong>Resultado</strong><span>Medición periódica</span></div><div><b>4</b><strong>Beneficio</strong><span>Evidencia y acumulado</span></div></div><button onClick={()=>registrar("SEGUIMIENTO_EJECUTIVO","Interés en seguimiento periódico de implementación y beneficios")}>Quiero seguimiento ejecutivo →</button></div>}
   {panel==="accion"&&<div className="guest-action-v8"><div className="guest-action-copy"><span>CÓMO LO LLEVARÍAMOS A SU EMPRESA</span><h2>De una señal a una mejora medible, sin entregar el diagnóstico antes de validarlo.</h2><p>La demostración enseña capacidad. Con sus datos validamos magnitud, evidencia y prioridad. El detalle operativo completo se desarrolla dentro del alcance contratado.</p></div>{Array.isArray(v?.metodologia)&&<div className="guest-method-mini">{v.metodologia.map((x:string,i:number)=><span key={x}><b>{i+1}</b>{x}</span>)}</div>}<div className="guest-next-actions guest-next-actions-v7"><button onClick={()=>registrar("EVALUAR_CON_MIS_DATOS","Solicita evaluación preliminar controlada")}><b>01</b><div><strong>Evaluar con mis datos</strong><p>Cuantificar oportunidad y evidencia sin revelar aún todo el diagnóstico.</p><em>Solicitar evaluación →</em></div></button><button onClick={()=>registrar("MOSTRAR_METODOLOGIA","Solicita conocer cómo se implementaría")}><b>02</b><div><strong>¿Cómo lo implementarían?</strong><p>Mostrar metodología, alcance, responsables, tiempos e indicadores.</p><em>Ver metodología →</em></div></button><button onClick={()=>registrar("SIGUIENTE_SESION","Solicita siguiente paso comercial")}><b>03</b><div><strong>Definir siguiente paso</strong><p>Registrar el interés para preparar una propuesta enfocada.</p><em>Continuar →</em></div></button></div></div>}
   {panel==="hallazgo"&&<section className="guest-v17-client"><div><span>CON SUS DATOS PODEMOS RESPONDER</span><h3>¿Qué oportunidades existen realmente en su entidad?</h3><p>Cuánto puede recuperar · dónde puede producir y facturar más · qué ciclos retrasan el ingreso · dónde reducir costos · dónde está concentrado el riesgo.</p></div><button onClick={()=>registrar("EVALUAR_CON_MIS_DATOS","Solicita evaluación preliminar con datos de la entidad")}>Evaluar mi entidad con datos reales →</button></section>}
   {v&&<div id="guest-presenter-share" className="guest-v18-share"><div><strong>✦ DESDE LA REUNIÓN</strong><span className="semantic-badge hecho">{v?.respuesta?"NUEVO":"EN VIVO"}</span></div><h3>{v?.titulo||topic.label}</h3>{v?.subtitulo&&<small>{v.subtitulo}</small>}{v?.respuesta?<p>{v.respuesta}</p>:Array.isArray(v?.contenido)&&<p>{v.contenido.slice(0,2).join(" · ")}</p>}</div>}
   <form className="guest-question-box guest-v18-question" onSubmit={enviarPregunta}><div><b>✦ Preguntar a ELIA</b><span>La pregunta llega a la cabina y queda asociada a este tema.</span></div><input value={guestQuestion} onChange={e=>setGuestQuestion(e.target.value)} placeholder="Pregunte por una cifra, evidencia u oportunidad…" /><button type="submit" disabled={!guestQuestion.trim()}>Preguntar →</button></form>
  </section>
  {interestMsg&&<div className="guest-interest-confirm">{interestMsg}</div>}<footer className="guest-footer guest-footer-v7"><span>Demo: cifras simuladas/estimadas. Resultados reales requieren validación con datos de la entidad.</span><strong>Sala {sala.codigo} · sincronización automática</strong></footer>
 </main>
}
