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

def answer_demo_question(db, organization_id: str, expediente_id: str, question: str, active_topic: str) -> dict[str, Any]:
    topics = _topics(question, active_topic)
    guides = [TOPIC_GUIDE[t] for t in topics if t in TOPIC_GUIDE]
    if not guides:
        guides = [TOPIC_GUIDE["facturacion"]]
    labels = " + ".join(g["label"] for g in guides)
    evidence = "; ".join(g["evidence"] for g in guides)
    needs = "; ".join(g["need"] for g in guides)
    q = _norm(question)
    cross = len(guides) > 1 or any(x in q for x in ("relacion", "cruza", "impacta", "conecta", "flujo", "depend", "extremo"))
    if cross:
        response = f"Sí. En esta demostración EIIAX puede cruzar {labels}. El caso ficticio permite mostrar {evidence}. Para comprobar esa relación en su IPS necesitaríamos {needs}."
    else:
        response = f"En {guides[0]['label']}, EIIAX puede demostrar {guides[0]['evidence']}. En esta reunión los resultados son SIMULADOS/ESTIMADOS; para responder con cifras reales de su IPS necesitaríamos {guides[0]['need']}."
    if any(x in q for x in ("cuanto", "valor", "porcentaje", "cifra", "recuperar", "ahorro")):
        response += " No extrapolaré una cifra ficticia como promesa: cualquier valor económico mostrado aquí es demostrativo y debe recalcularse con información real."
    return {
        "respuesta": response,
        "tema_activo": active_topic,
        "temas_relacionados": topics,
        "modo": "DEMO",
        "semantica": "SIMULADO_ESTIMADO_NO_VERIFICADO",
        "fuente": "Caso ficticio preparado y presentación demo del expediente",
        "requiere_datos_reales": True,
        "empresa_demo": None,
    }
