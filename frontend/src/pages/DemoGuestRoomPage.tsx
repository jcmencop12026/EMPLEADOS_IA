import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { fetchDemoSalaPublic, sendDemoGuestInterest, type DemoSala } from "../api";

const GUEST_IMPACT = [["↗","Ingresos"],["↘","Pérdidas"],["◉","Costos"],["⚡","Productividad"],["◇","Riesgos"]];
const IMPACT_DETAIL:any={
 Ingresos:{value:"+ $185 M",title:"Potencial de nuevos ingresos",text:"Capacidad disponible y demanda no capturada.",action:"Priorizar crecimiento"},
 "Pérdidas":{value:"$742 M",title:"Valor expuesto en cartera",text:"Cartera envejecida y devoluciones requieren intervención.",action:"Reducir fuga"},
 Costos:{value:"31%",title:"Concentración relevante",text:"Dependencias que pueden afectar costo y margen.",action:"Optimizar costo"},
 Productividad:{value:"18,7 días",title:"Oportunidad de ciclo",text:"Reducir tiempos libera capacidad operativa.",action:"Acelerar proceso"},
 Riesgos:{value:"2 alertas",title:"Riesgos priorizados",text:"Concentración y cartera requieren seguimiento ejecutivo.",action:"Ver controles"}
};

export function DemoGuestRoomPage(){
 const {codigo=""}=useParams(); const [sp]=useSearchParams(); const token=sp.get("token")||"";
 const [sala,setSala]=useState<DemoSala|null>(null); const [error,setError]=useState<string|null>(null); const [selected,setSelected]=useState<number|null>(null); const [interestMsg,setInterestMsg]=useState<string|null>(null); const [impact,setImpact]=useState("Ingresos"); const [panel,setPanel]=useState<"oportunidades"|"indicadores"|"acciones">("oportunidades"); const [decision,setDecision]=useState<string|null>(null); const [focus,setFocus]=useState(0);
 useEffect(()=>{let stop=false; const load=()=>fetchDemoSalaPublic(codigo,token).then(x=>{if(!stop){setSala(x);setError(null)}}).catch(e=>{if(!stop)setError(e.message)}); load(); const id=setInterval(load,1500); return()=>{stop=true;clearInterval(id)}},[codigo,token]);
 if(error)return <main className="guest-room"><h1>EIIAX · Sala ejecutiva</h1><p className="error">{error}</p></main>;
 if(!sala)return <main className="guest-room"><h1>EIIAX · Sala ejecutiva</h1><p>Conectando con la reunión…</p></main>;
 const v=sala.visible as any; const findings=Array.isArray(v?.contenido)?v.contenido:[]; const registrar=async(accion:string,detalle:string)=>{try{await sendDemoGuestInterest(codigo,token,accion,impact,detalle);setInterestMsg("✓ Interés enviado al presentador");setTimeout(()=>setInterestMsg(null),3500)}catch{setInterestMsg("No fue posible registrar el interés")}};
 return <main className="guest-room guest-room-v2 guest-room-v3 guest-room-v4 guest-room-v7">
 <header className="guest-executive-header">
  <div className="guest-logo-plate"><img src="/assets/identity/eiaax-logo-approved.png" alt="EIIAX" /></div>
  <div className="guest-executive-title"><span className="semantic-badge hecho">● REUNIÓN EN VIVO · {v?.nivel||"DEMO"}</span><h1>{v?.titulo||"Inteligencia para decidir y mejorar"}</h1><p>{v?.subtitulo||"IA aplicada para convertir datos en decisiones con impacto."}</p></div>
  <div className="guest-impact guest-impact-top">{GUEST_IMPACT.map(([icon,label])=><button type="button" key={label} className={impact===label?"active":""} onClick={()=>setImpact(label)}><b>{icon}</b>{label}</button>)}</div>
 </header>
 <section className="guest-decision-strip">
   <div><span>IMPACTO ACTIVO · {impact.toUpperCase()}</span><strong>{IMPACT_DETAIL[impact].value}</strong><p>{IMPACT_DETAIL[impact].title}</p><small>{IMPACT_DETAIL[impact].text}</small></div>
   <button onClick={()=>{setPanel("oportunidades");setDecision(IMPACT_DETAIL[impact].action);registrar("QUIERO_PROFUNDIZAR",IMPACT_DETAIL[impact].title)}}>Quiero profundizar esto →</button>
 </section>
 <nav className="guest-actionbar guest-actionbar-v7">
   <button className={panel==="oportunidades"?"active":""} onClick={()=>setPanel("oportunidades")}>◈ Qué encontramos</button>
   <button className={panel==="indicadores"?"active":""} onClick={()=>setPanel("indicadores")}>▥ Por qué importa</button>
   <button className={panel==="acciones"?"active":""} onClick={()=>setPanel("acciones")}>✓ Qué hacemos ahora</button>
   {decision&&<span className="guest-decision-inline">✓ {decision}</span>}
 </nav>
 <section className="guest-workspace">
 {panel==="oportunidades"&&<>
   <div className="guest-story"><span>OPORTUNIDAD PRIORITARIA</span><h2>{findings[focus]?.replace(/^Oportunidad:\\s*/,"")||"Seleccione una oportunidad"}</h2><p>{focus%3===0?"Hay capacidad o valor disponible que hoy no se está convirtiendo completamente en resultado.":focus%3===1?"La brecha detectada permite enfocar una decisión concreta sin revisar toda la operación.":"El hallazgo conecta impacto económico, proceso y una acción verificable."}</p><div className="guest-story-impact"><b>{IMPACT_DETAIL[impact].value}</b><small>{IMPACT_DETAIL[impact].title}</small></div><button onClick={()=>setSelected(focus)}>Ver explicación ejecutiva →</button></div>
   <div className="guest-opportunity-rail">{findings.slice(0,6).map((x:string,i:number)=><button key={i} className={focus===i?"active":""} onClick={()=>{setFocus(i);setSelected(null)}}><b>{String(i+1).padStart(2,"0")}</b><span>{x.replace(/^Oportunidad:\\s*/,"")}</span></button>)}</div>
 </>}
 {panel==="indicadores"&&<div className="guest-manager-kpis guest-manager-kpis-v7"><article><span>INGRESOS</span><b>$4.860 M</b><p>Facturación observada en 6 meses</p><em>Base para dimensionar el impacto</em></article><article><span>VELOCIDAD</span><b>18,7 días</b><p>Factura → radicación</p><em>Reducir ciclo acelera caja</em></article><article><span>CARTERA</span><b>$742 M</b><p>Mayor a 90 días</p><em>Priorizar por recuperabilidad</em></article><article><span>CONCENTRACIÓN</span><b>31%</b><p>En un pagador</p><em>Riesgo y oportunidad contractual</em></article></div>}
 {panel==="acciones"&&<>{Array.isArray(v?.metodologia)&&<div className="guest-method-mini">{v.metodologia.map((x:string,i:number)=><span key={x}><b>{i+1}</b>{x}</span>)}</div>}<div className="guest-next-actions guest-next-actions-v7"><button onClick={()=>{setPanel("oportunidades");setDecision("Oportunidad priorizada");registrar("PRIORIZAR_OPORTUNIDAD",findings[focus]||impact)}}><b>01</b><div><strong>Elegir dónde actuar</strong><p>Priorizamos el hallazgo con mayor valor y posibilidad de intervención.</p><em>Priorizar ahora →</em></div></button><button onClick={()=>{setDecision("Validación con datos IPS solicitada");registrar("EVALUAR_CON_MIS_DATOS","Solicita ejercicio preliminar controlado")}}><b>02</b><div><strong>Validar con datos de la IPS</strong><p>Pasamos de la simulación a magnitud, evidencia y responsables reales.</p><em>Solicitar ejercicio preliminar →</em></div></button><button onClick={()=>{setDecision("Siguiente sesión marcada como interés");registrar("SIGUIENTE_SESION","Solicita conocer metodología y siguiente paso")}}><b>03</b><div><strong>Convertirlo en plan</strong><p>Definimos alcance, responsables, evidencia y siguiente decisión.</p><em>Registrar siguiente paso →</em></div></button></div></>}
 {selected!==null&&findings[selected]&&<aside className="guest-drilldown guest-drilldown-v7"><button onClick={()=>setSelected(null)}>×</button><span>LECTURA EJECUTIVA</span><h3>{findings[selected].replace(/^Oportunidad:\\s*/,"")}</h3><p>EIIAX conecta este hallazgo con el proceso activo para orientar una decisión, no solo mostrar un dato.</p><strong>Con datos reales de la IPS</strong><p>Validamos magnitud, evidencia, responsable, impacto económico y acción antes de presentarlo como resultado real.</p></aside>}
 {v?.respuesta&&<div className="elia-answer guest-elia"><strong>ELIA · RESPUESTA EN VIVO</strong><p>{v.respuesta}</p></div>}
 </section>
 {interestMsg&&<div className="guest-interest-confirm">{interestMsg}</div>}<footer className="guest-footer guest-footer-v7"><span>Demo con datos simulados/estimados.</span><strong>Sala {sala.codigo} · sincronización automática</strong></footer>
 </main>
}