"""Copiloto ELIA para reuniones demo: respuestas trazables y sin inventar datos."""
from __future__ import annotations

import re
from typing import Any


TOPIC_ALIASES = {
    "facturacion": ("factura", "facturacion", "ingreso", "servicio", "mercado", "demanda", "contratacion", "cartera", "radicacion", "pago", "dinero", "recuper"),
    "glosas": ("glosa", "devolucion", "causal", "motivo", "objecion", "reincidencia"),
    "rrhh": ("rrhh", "talento", "personal", "empleado", "productividad", "ausent", "rotacion", "turno", "hora extra"),
    "operaciones": ("operacion", "capacidad", "proceso", "reproceso", "error", "flujo", "cuello", "espera", "dependencia", "sla", "tiempo"),
    "compras": ("costo", "precio", "compra", "inventario", "proveedor", "stock", "vencimiento", "abaste"),
    "sistemas": ("sistema", "riesgo", "ciber", "seguridad", "continuidad", "integracion", "interfaz", "tecnologia", "piiax", "manual", "dato"),
}

def _norm(value: str) -> str:
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", value.lower()) if unicodedata.category(c) != "Mn")

def _topics(question: str, active: str) -> list[str]:
    q = _norm(question)
    found = [topic for topic, words in TOPIC_ALIASES.items() if any(word in q for word in words)]
    if active and active not in found:
        found.insert(0, active)
    return found[:3]

TOPIC_GUIDE = {
 "facturacion": {"label":"Ingresos, facturación y cartera","evidence":"servicios vs. mercado/demanda, capacidad subutilizada, contratación, radicación, concentración por pagador, edad de cartera y recuperación","need":"portafolio de servicios, producción/capacidad, contratación, facturas, pagador, fechas, valor, saldo, pagos y rechazos"},
 "glosas": {"label":"Glosas y devoluciones","evidence":"Pareto por frecuencia y valor, motivos de devolución, servicios/pagadores recurrentes, tiempos de respuesta, pérdida evitable y recuperación","need":"factura, servicio, pagador, causal/motivo, fechas, valor glosado/devuelto, respuesta IPS y recuperación"},
 "rrhh": {"label":"Personas y productividad","evidence":"capacidad, productividad, ausentismo, rotación, carga por rol, horas extra y automatización","need":"planta anonimizada, cargos, áreas, turnos, horas, ausentismo, rotación, novedades y volúmenes de trabajo"},
 "operaciones": {"label":"Procesos, flujos y operaciones","evidence":"reprocesos, errores, tiempos, esperas, dependencias, cuellos de botella, capacidad y SLA","need":"mapa de procesos, eventos por etapa, tiempos, responsables, volúmenes, incidencias, reprocesos y puntos de transferencia entre áreas"},
 "compras": {"label":"Costos, compras e inventario","evidence":"costos, rotación, faltantes, vencimientos, compras urgentes y dependencia/precios de proveedores","need":"compras, precios, proveedores, inventario, movimientos, consumos, quiebres, vencimientos y costos asociados"},
 "sistemas": {"label":"Sistemas, riesgos e integraciones","evidence":"riesgos informáticos/ciberseguridad, continuidad, integraciones, trabajo manual, dependencias y duplicidad de datos","need":"inventario de aplicaciones/activos, interfaces, responsables, incidencias, continuidad, controles y procesos manuales; nunca credenciales"},
}

CONCERN_GUIDE = {
 "infraestructura":{"match":("infraestructura","servidor","nube","on premise","hosting"),"meaning":"capacidad, arquitectura, disponibilidad y crecimiento de la plataforma","example":"identificar un servidor o enlace sin redundancia que pueda interrumpir un proceso crítico","need":"inventario de infraestructura, capacidad, utilización, disponibilidad, dependencias y esquema de respaldo","intervention":"levanta arquitectura y dependencias, mide capacidad/disponibilidad, prioriza puntos únicos de falla y propone una ruta de mejora","measure":"disponibilidad %, utilización %, incidentes, tiempo de recuperación y costo de indisponibilidad"},
 "proteccion_datos":{"match":("proteccion de datos","privacidad","datos personales","dato sensible"),"meaning":"gobierno del dato, finalidad, acceso, minimización, retención y trazabilidad","example":"detectar información sensible disponible para perfiles que no la requieren","need":"clasificación de datos, finalidades, perfiles, accesos, flujos, retención y controles; nunca contraseñas","intervention":"mapea flujos y accesos, identifica exposición innecesaria y define controles, evidencias y responsables","measure":"accesos innecesarios, hallazgos, cobertura de controles y tiempos de atención"},
 "ciberseguridad":{"match":("ciberseguridad","ciber","seguridad informatica","ataque","vulnerabilidad"),"meaning":"prevención, detección, respuesta y recuperación frente a eventos de seguridad","example":"priorizar activos críticos sin cobertura suficiente de respaldo, monitoreo o respuesta","need":"activos, criticidad, incidentes, controles, respaldos, monitoreo y planes de respuesta","intervention":"construye matriz de riesgo, correlaciona incidentes/activos/controles y prioriza mitigaciones verificables","measure":"incidentes, cobertura de controles, tiempo de detección, tiempo de recuperación y riesgo residual"},
 "integraciones":{"match":("integracion","interoperabilidad","api","interfaz","his","erp"),"meaning":"intercambio confiable de información entre aplicaciones sin redigitación ni pérdida de trazabilidad","example":"reemplazar una transferencia manual entre HIS y facturación por un flujo controlado y auditable","need":"mapa de aplicaciones, interfaces, formatos, frecuencia, responsables, errores y volúmenes","intervention":"mapea origen-destino, identifica pasos manuales, define integración priorizada y controla errores/extremos","measure":"interfaces manuales, horas de redigitación, errores, latencia y disponibilidad"},
 "continuidad":{"match":("continuidad","backup","respaldo","recuperacion","disponibilidad","sla"),"meaning":"capacidad de mantener o recuperar servicios críticos ante fallas","example":"medir cuánto tarda en recuperarse un servicio crítico y si el respaldo realmente permite restaurarlo","need":"servicios críticos, RTO/RPO definidos, respaldos, pruebas de restauración, dependencias e incidentes","intervention":"prioriza servicios, valida dependencias y evidencia de recuperación, y estructura seguimiento de continuidad","measure":"RTO, RPO, disponibilidad %, éxito de restauraciones y tiempo fuera de servicio"},
 "roi":{"match":("roi","retorno","inversion","recuperacion de inversion","flujo de caja"),"meaning":"relación entre inversión, beneficio verificable y tiempo para recuperar recursos","example":"comparar costo de intervención con ahorro de reproceso o recuperación incremental medible","need":"costos actuales, inversión, volúmenes, pérdidas/ahorros, horizonte y línea base","intervention":"construye línea base, separa supuestos de datos reales y mide beneficio antes/proyectado/real","measure":"COP invertidos, COP recuperados/ahorrados, ROI % y meses de recuperación"},
 "personas":{"match":("puesto","empleo","personal","capacitacion","gestion del cambio","automatizacion","carga laboral"),"meaning":"impacto de la intervención sobre carga, capacidades, responsabilidades y adopción","example":"automatizar una tarea repetitiva y reasignar tiempo a validación o gestión de mayor valor","need":"roles, tareas, volúmenes, tiempos, turnos, competencias y novedades agregadas","intervention":"mide carga, detecta repetición, define tareas automatizables y plan de adopción con supervisión humana","measure":"horas liberadas, productividad, horas extra, adopción y errores/reprocesos"},
 "operacion":{"match":("reproceso","cuello","sla","tiempo de ciclo","capacidad","operacion","proceso"),"meaning":"desempeño extremo a extremo del proceso, sus esperas, errores y restricciones","example":"localizar una etapa que acumula cola y devuelve casos a la fase anterior","need":"eventos por etapa, tiempos, responsables, volúmenes, incidencias y reprocesos","intervention":"reconstruye flujo, cuantifica esperas/reprocesos, identifica causa y mide la intervención","measure":"tiempo de ciclo, reproceso %, SLA, capacidad utilizada y casos pendientes"},
}

def _specific_concern(question: str):
    q=_norm(question)
    for key,item in CONCERN_GUIDE.items():
        if any(_norm(term) in q for term in item["match"]):
            return key,item
    return None,None

def answer_demo_question(db, organization_id: str, expediente_id: str, question: str, active_topic: str) -> dict[str, Any]:
    topics = _topics(question, active_topic)
    guides = [TOPIC_GUIDE[t] for t in topics if t in TOPIC_GUIDE] or [TOPIC_GUIDE.get(active_topic, TOPIC_GUIDE["facturacion"])]
    key, concern = _specific_concern(question)
    if concern:
        response = (
            f"INQUIETUD · {key.replace('_',' ').upper()}\n"
            f"Qué significa: {concern['meaning']}.\n"
            f"Por qué importa: permite convertir una preocupación de la audiencia en riesgo, costo, capacidad o resultado verificable.\n"
            f"Ejemplo: {concern['example']}.\n"
            f"Datos mínimos: {concern['need']}.\n"
            f"Cómo interviene EIIAX: {concern['intervention']}.\n"
            f"Cómo se mide: {concern['measure']}."
        )
    else:
        g=guides[0]
        response=(
            f"FOCO · {g['label']}\n"
            f"Qué analizaría EIIAX: {g['evidence']}.\n"
            f"Datos mínimos: {g['need']}.\n"
            "Intervención EIIAX: construir línea base, cruzar procesos/datos, identificar causas y responsables, priorizar acciones y medir antes / objetivo / resultado.\n"
            "Resultado medible: el indicador y su valor se definen con la línea base; en demo no se convierte una cifra ficticia en promesa."
        )
    if any(x in _norm(question) for x in ("cuanto","valor","porcentaje","cifra","recuperar","ahorro","roi")):
        response += "\nCriterio económico: toda cifra demo es ilustrativa y se recalcula con datos reales antes de asumir compromisos."
    return {"respuesta":response,"tema_activo":active_topic,"temas_relacionados":topics,"modo":"DEMO","semantica":"SIMULADO_ESTIMADO_NO_VERIFICADO","fuente":"Caso ficticio preparado y presentación demo del expediente","requiere_datos_reales":True,"empresa_demo":None}
