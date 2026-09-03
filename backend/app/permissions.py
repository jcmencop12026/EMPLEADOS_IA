"""Catálogo de permisos y roles — CURSOR-840.

Modelo de autorización (runtime):
- Fuente de roles: tabla `roles` (org-específico prioriza sobre global de sistema).
- Fuente de permisos: tabla `role_permissions` vía `role_permission_codes()`.
- Bootstrap: `seed_permissions.bootstrap_permissions()` crea roles/permisos de sistema.
- Política: DENY BY DEFAULT / FAIL CLOSED — sin fallback permisivo en runtime.
"""
from __future__ import annotations

import logging

from fastapi import Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Permission, Role, RolePermission, User

logger = logging.getLogger(__name__)

EMPLOYEE_PERMISSIONS = {
    "employee.view",
    "employee.create",
    "employee.edit",
    "employee.test",
    "employee.certify",
    "employee.approve",
    "employee.publish",
    "employee.activate",
    "employee.pause",
    "employee.retire",
    "employee.rollback",
    "employee.train",
    "employee.admin",
}

NOTIFICATION_PERMISSIONS = {
    "notification.view",
    "notification.manage",
    "notification.acknowledge",
    "alert_rule.view",
    "alert_rule.manage",
}

COMMUNICATIONS_PERMISSIONS = {
    "communications.view",
    "communications.send",
    "communications.schedule",
    "communications.template.manage",
    "communications.rule.manage",
    "communications.channel.manage",
    "communications.history.view",
}

ADMIN_PERMISSIONS = {
    "admin.user.view",
    "admin.user.create",
    "admin.user.edit",
    "admin.user.activate",
    "admin.user.deactivate",
    "admin.user.reset_password",
    "admin.role.view",
    "admin.role.create",
    "admin.role.edit",
    "admin.role.assign_permissions",
    "admin.organization.view",
    "admin.organization.edit",
    "admin.config.view",
    "admin.config.edit",
    "admin.security.view",
}

SECURITY_PERMISSIONS = {
    "seguridad.view",
    "seguridad.manage_policy",
    "seguridad.revoke_sessions",
    "seguridad.audit",
}

IDENTITY_PERMISSIONS = {
    "identidad.view",
    "identidad.manage",
    "identidad.test",
    "identidad.activate",
    "identidad.audit",
}

OPERATIONS_PERMISSIONS = {
    "operations.view",
    "operations.execute",
    "operations.manage",
    "operations.cancel",
    "operations.reassign",
    "operations.approve",
}

AUTOMATION_PERMISSIONS = {
    "automation.view",
    "automation.create",
    "automation.edit",
    "automation.activate",
    "automation.pause",
    "automation.run",
    "automation.delete",
    "automation.view_runs",
}

AUDIT_PERMISSIONS = {
    "audit.view",
}

CAPABILITY_PERMISSIONS = {
    "capability.view",
    "capability.manage",
}

TOOL_PERMISSIONS = {
    "tool.view",
    "tool.manage",
}

SALUD_PERMISSIONS = {
    "salud.cargar_datos",
    "salud.ejecutar_analisis",
    "salud.consultar_diagnostico",
    "salud.aceptar_recomendaciones",
    "salud.administrar_experiencia",
}

KNOWLEDGE_PERMISSIONS = {
    "knowledge.view",
    "knowledge.manage",
    "knowledge.upload",
    "knowledge.delete",
    "knowledge.use",
}

TEST_LAB_PERMISSIONS = {
    "test_lab.view",
    "test_lab.run",
}

LLM_PERMISSIONS = {
    "llm.view",
    "llm.manage",
    "llm.use",
}

FINOPS_PERMISSIONS = {
    "finops.view",
    "finops.manage",
    "finops.budget",
    "finops.rates",
    "finops.planner.simulate",
    "finops.planner.configure",
    "finops.margin.view",
    "finops.economy.recommend",
}

FINOPS_ECONOMY_PRIVATE_PERMISSIONS = {
    "finops.economy.private",
}

OPORTUNIDADES_PERMISSIONS = {
    "oportunidades.view",
    "oportunidades.manage",
    "oportunidades.evaluate",
    "oportunidades.approve",
    "oportunidades.activate",
}


LINEA_BASE_PERMISSIONS = {
    "linea_base.view",
    "linea_base.manage",
    "linea_base.validate",
}

VALORACION_PERMISSIONS = {
    "valoracion.view",
    "valoracion.manage",
    "valoracion.validate",
    "valoracion.roi",
}

DIAGNOSTICOS_PERMISSIONS = {
    "diagnosticos.view",
    "diagnosticos.generate",
    "diagnosticos.validate",
    "diagnosticos.manage",
}

EVALUACION_PERMISSIONS = {
    "evaluacion.view",
    "evaluacion.manage",
    "evaluacion.evaluate",
    "evaluacion.visibility",
    "evaluacion.vista_entidad",
    "evaluacion.accion.request",
    "evaluacion.accion.approve",
    "evaluacion.indicadores.manage",
}

INTELIGENCIA_EMPRESARIAL_PERMISSIONS = {
    "inteligencia_empresarial.view",
    "inteligencia_empresarial.manage",
}

INTELIGENCIA_EXTERNA_PERMISSIONS = {
    "inteligencia_externa.view",
    "inteligencia_externa.manage",
    "inteligencia_externa.ingest",
    "inteligencia_externa.validate",
}

DATOS_PERMISSIONS = {
    "datos.view",
    "datos.classify",
    "datos.manage_policy",
    "datos.export",
    "datos.audit",
    "datos.requests",
    "datos.retention",
}

INTEGRATION_PERMISSIONS = {
    "integraciones.view",
    "integraciones.create",
    "integraciones.configure",
    "integraciones.test",
    "integraciones.execute",
    "integraciones.manage_secrets",
}

APRENDIZAJE_PERMISSIONS = {
    "aprendizaje.view",
    "aprendizaje.evaluate",
    "aprendizaje.recalibrate",
    "aprendizaje.approve",
}

OPTIMIZACION_PERMISSIONS = {
    "optimizacion.view",
    "optimizacion.simulate",
    "optimizacion.create",
    "optimizacion.approve",
    "optimizacion.execute",
    "optimizacion.configure",
}

COMMERCIAL_PERMISSIONS = {
    "comercial.view",
    "comercial.simulate",
    "comercial.create",
    "comercial.approve",
    "comercial.manage_plans",
}

TCO_PERMISSIONS = {
    "tco.view",
    "tco.manage",
    "tco.simulate",
    "proveedores.view",
    "proveedores.manage",
    "alianzas.view",
    "alianzas.manage",
}

IMPLEMENTACION_PERMISSIONS = {
    "implementacion.view",
    "implementacion.manage",
    "implementacion.approve_go_live",
    "exito_cliente.view",
    "exito_cliente.manage",
    "exito_cliente.review",
}

SEGMENTATION_PERMISSIONS = {
    "segmentacion.view",
    "segmentacion.manage",
    "planes.view",
    "planes.manage",
    "planes.recommend",
    "planes.approve_discount",
}

PLATFORM_PERMISSIONS = {
    "platform.organization.view",
    "platform.organization.create",
    "platform.organization.manage",
}

EMPLOYEE_AUDIT_PERMISSIONS = {
    "auditor_empleados.view",
    "auditor_empleados.execute",
    "auditor_empleados.configure",
}

CONTROL_CENTER_PERMISSIONS = {
    "control_center.view",
}

GOBIERNO_OPERACIONAL_PERMISSIONS = {
    "gobierno.view",
    "gobierno.manage",
    "gobierno.execute",
    "gobierno.approve",
    "gobierno.visibility",
    "gobierno.ia_policy",
    "gobierno.audit",
    "gobierno.confianza.view",
    "gobierno.clasificacion.view",
    "gobierno.clasificacion.assign",
    "gobierno.trazabilidad.view",
    "gobierno.evidencia.view",
    "gobierno.evidencia.link",
    "gobierno.auditoria.consulta",
}

NEGOCIO_PERMISSIONS = {
    "negocio.view",
    "negocio.manage",
    "negocio.economy.private",
    "negocio.proposal.approve",
    "negocio.proposal.present",
    "negocio.contract",
}

CONTINUIDAD_COMERCIAL_PERMISSIONS = {
    "continuidad_comercial.view",
    "continuidad_comercial.manage",
    "continuidad_comercial.close",
}

TRANSFORMACION_PERMISSIONS = {
    "transformacion.view",
    "transformacion.manage",
    "transformacion.execute",
}

STRATEGIC_CONTROL_PERMISSIONS = {
    "strategic_control.view",
    "strategic_control.economia_privada",
}

FLUJO_COMERCIAL_PERMISSIONS = {
    "flujo_comercial.view",
    "flujo_comercial.manage",
}

ESPACIO_EXTERNO_PERMISSIONS = {
    "espacio_externo.manage",
    "espacio_externo.publish",
    "espacio_externo.acceso",
    "espacio_externo.portal",
    "espacio_externo.entregar",
}

RESULTADOS_PERMISSIONS = {
    "resultados.view",
    "resultados.manage",
    "resultados.validate",
    "resultados.informe.generate",
}

PARTNER_PERMISSIONS = {
    "partners.view",
    "partners.manage",
    "partners.org.grant",
    "partners.user.assign",
    "partners.audit",
}

CONTINUIDAD_PERMISSIONS = {
    "continuidad.view",
    "continuidad.manage",
    "continuidad.activate",
    "continuidad.test",
}

INCIDENTES_PERMISSIONS = {
    "incidentes.view",
    "incidentes.manage",
    "incidentes.close",
}

BACKUPS_PERMISSIONS = {
    "backups.view",
    "backups.manage",
    "backups.verify",
}

SUPPORT_PERMISSIONS = {
    "support.view",
    "support.create",
    "support.assign",
    "support.update",
    "support.resolve",
    "support.close",
    "support.admin",
}

ALL_PERMISSIONS: dict[str, tuple[str, str]] = {
    "employee.view": ("Empleados IA", "Ver directorio de empleados"),
    "employee.create": ("Empleados IA", "Crear empleados"),
    "employee.edit": ("Empleados IA", "Editar empleados"),
    "employee.test": ("Empleados IA", "Ejecutar pruebas"),
    "employee.certify": ("Empleados IA", "Certificar empleados"),
    "employee.approve": ("Empleados IA", "Aprobar cambios críticos de empleados"),
    "employee.publish": ("Empleados IA", "Publicar empleados"),
    "employee.activate": ("Empleados IA", "Activar empleados"),
    "employee.pause": ("Empleados IA", "Pausar empleados"),
    "employee.retire": ("Empleados IA", "Retirar empleados"),
    "employee.rollback": ("Empleados IA", "Revertir versión de empleado"),
    "employee.train": ("Empleados IA", "Capacitar empleados"),
    "employee.admin": ("Empleados IA", "Administrar empleados"),
    "auditor_empleados.view": ("Auditor Empleados IA", "Ver auditorías y salud de empleados"),
    "auditor_empleados.execute": ("Auditor Empleados IA", "Ejecutar auditorías de empleados"),
    "auditor_empleados.configure": ("Auditor Empleados IA", "Configurar política de auditoría"),
    "notification.view": ("Notificaciones", "Ver notificaciones"),
    "notification.manage": ("Notificaciones", "Gestionar notificaciones"),
    "notification.acknowledge": ("Notificaciones", "Confirmar notificaciones"),
    "alert_rule.view": ("Alertas", "Ver reglas de alerta"),
    "alert_rule.manage": ("Alertas", "Gestionar reglas de alerta"),
    "communications.view": ("Comunicaciones", "Ver centro de comunicaciones"),
    "communications.send": ("Comunicaciones", "Enviar comunicaciones"),
    "communications.schedule": ("Comunicaciones", "Programar y cancelar comunicaciones"),
    "communications.template.manage": ("Comunicaciones", "Gestionar plantillas"),
    "communications.rule.manage": ("Comunicaciones", "Gestionar reglas de comunicación"),
    "communications.channel.manage": ("Comunicaciones", "Gestionar canales"),
    "communications.history.view": ("Comunicaciones", "Ver historial detallado"),
    "operations.view": ("Operaciones", "Ver ejecuciones y operaciones"),
    "operations.execute": ("Operaciones", "Ejecutar solicitudes"),
    "operations.manage": ("Operaciones", "Gestionar operaciones"),
    "operations.cancel": ("Operaciones", "Cancelar operaciones"),
    "operations.reassign": ("Operaciones", "Reasignar operaciones"),
    "operations.approve": ("Operaciones", "Aprobar solicitudes"),
    "automation.view": ("Automatizaciones", "Ver automatizaciones"),
    "automation.create": ("Automatizaciones", "Crear automatizaciones"),
    "automation.edit": ("Automatizaciones", "Editar automatizaciones"),
    "automation.activate": ("Automatizaciones", "Activar automatizaciones"),
    "automation.pause": ("Automatizaciones", "Pausar automatizaciones"),
    "automation.run": ("Automatizaciones", "Ejecutar automatizaciones"),
    "automation.delete": ("Automatizaciones", "Eliminar automatizaciones"),
    "automation.view_runs": ("Automatizaciones", "Ver ejecuciones de automatizaciones"),
    "audit.view": ("Auditoría", "Ver registros de auditoría"),
    "admin.user.view": ("Administración", "Ver usuarios"),
    "admin.user.create": ("Administración", "Crear usuarios"),
    "admin.user.edit": ("Administración", "Editar usuarios"),
    "admin.user.activate": ("Administración", "Activar usuarios"),
    "admin.user.deactivate": ("Administración", "Desactivar usuarios"),
    "admin.user.reset_password": ("Administración", "Restablecer contraseña"),
    "admin.role.view": ("Administración", "Ver roles"),
    "admin.role.create": ("Administración", "Crear roles"),
    "admin.role.edit": ("Administración", "Editar roles"),
    "admin.role.assign_permissions": ("Administración", "Asignar permisos a roles"),
    "admin.organization.view": ("Administración", "Ver organización"),
    "admin.organization.edit": ("Administración", "Editar organización"),
    "admin.config.view": ("Administración", "Ver configuración"),
    "admin.config.edit": ("Administración", "Editar configuración"),
    "admin.security.view": ("Administración", "Ver panel de seguridad"),
    "seguridad.view": ("Seguridad", "Ver resumen de seguridad de la organización"),
    "seguridad.manage_policy": ("Seguridad", "Gestionar políticas de seguridad"),
    "seguridad.revoke_sessions": ("Seguridad", "Revocar sesiones de usuarios"),
    "seguridad.audit": ("Seguridad", "Consultar eventos de seguridad"),
    "identidad.view": ("Identidad", "Consultar proveedores y políticas SSO"),
    "identidad.manage": ("Identidad", "Configurar identidad empresarial"),
    "identidad.test": ("Identidad", "Probar proveedores de identidad"),
    "identidad.activate": ("Identidad", "Activar o desactivar proveedores"),
    "identidad.audit": ("Identidad", "Consultar auditoría de login SSO"),
    "capability.view": ("Capacidades", "Ver catálogo de capacidades"),
    "capability.manage": ("Capacidades", "Gestionar capacidades"),
    "tool.view": ("Herramientas", "Ver catálogo de herramientas"),
    "tool.manage": ("Herramientas", "Gestionar herramientas"),
    "knowledge.view": ("Conocimiento", "Ver fuentes de conocimiento"),
    "knowledge.manage": ("Conocimiento", "Gestionar fuentes de conocimiento"),
    "knowledge.upload": ("Conocimiento", "Cargar documentos"),
    "knowledge.delete": ("Conocimiento", "Eliminar documentos"),
    "knowledge.use": ("Conocimiento", "Consultar conocimiento"),
    "salud.cargar_datos": ("Salud IPS", "Cargar datos de salud"),
    "salud.ejecutar_analisis": ("Salud IPS", "Ejecutar análisis de salud"),
    "salud.consultar_diagnostico": ("Salud IPS", "Consultar diagnóstico IPS"),
    "salud.aceptar_recomendaciones": ("Salud IPS", "Aceptar recomendaciones"),
    "salud.administrar_experiencia": ("Salud IPS", "Administrar experiencia de salud"),
    "test_lab.view": ("Test Lab", "Ver ejecuciones de Test Lab"),
    "test_lab.run": ("Test Lab", "Ejecutar pruebas en Test Lab"),
    "finops.view": ("FinOps", "Ver costos y valor"),
    "finops.manage": ("FinOps", "Gestionar costos y valor"),
    "finops.budget": ("FinOps", "Gestionar presupuestos"),
    "finops.rates": ("FinOps", "Gestionar tarifas"),
    "finops.planner.simulate": ("FinOps", "Simular consumo y capacidad IA"),
    "finops.planner.configure": ("FinOps", "Configurar planificador de consumo IA"),
    "finops.margin.view": ("FinOps", "Ver margen comercial"),
    "finops.economy.private": ("FinOps", "Ver economía privada operador"),
    "finops.economy.recommend": ("FinOps", "Generar recomendaciones de precio (borrador)"),
    "llm.view": ("Proveedores IA", "Ver proveedores de inferencia"),
    "llm.manage": ("Proveedores IA", "Administrar proveedores de inferencia"),
    "llm.use": ("Proveedores IA", "Ejecutar inferencia LLM"),
    "oportunidades.view": ("Oportunidades", "Ver centro de oportunidades"),
    "oportunidades.manage": ("Oportunidades", "Gestionar oportunidades"),
    "oportunidades.evaluate": ("Oportunidades", "Evaluar y priorizar oportunidades"),
    "oportunidades.approve": ("Oportunidades", "Aprobar oportunidades"),
    "oportunidades.activate": ("Oportunidades", "Activar oportunidades"),
    "linea_base.view": ("Línea base", "Consultar líneas base e impacto"),
    "linea_base.manage": ("Línea base", "Crear línea base y registrar mediciones"),
    "linea_base.validate": ("Línea base", "Validar impacto y atribución"),
    "valoracion.view": ("Valoración económica", "Consultar valoración de oportunidades"),
    "valoracion.manage": ("Valoración económica", "Crear y modificar valoraciones"),
    "valoracion.validate": ("Valoración económica", "Validar valoraciones"),
    "valoracion.roi": ("Valoración económica", "Consultar retorno y beneficio neto"),
    "diagnosticos.view": ("Diagnósticos", "Consultar diagnósticos transversales"),
    "diagnosticos.generate": ("Diagnósticos", "Generar diagnósticos"),
    "diagnosticos.validate": ("Diagnósticos", "Validar diagnósticos"),
    "diagnosticos.manage": ("Diagnósticos", "Administrar configuración de diagnóstico"),
    "evaluacion.view": ("Evaluación EIAAX", "Consultar expedientes de evaluación"),
    "evaluacion.manage": ("Evaluación EIAAX", "Crear y editar expedientes de evaluación"),
    "evaluacion.evaluate": ("Evaluación EIAAX", "Ejecutar evaluaciones y registrar hallazgos"),
    "evaluacion.visibility": ("Evaluación EIAAX", "Gestionar visibilidad para entidad"),
    "evaluacion.vista_entidad": ("Evaluación EIAAX", "Ver vista entidad del expediente"),
    "evaluacion.accion.request": ("Evaluación EIAAX", "Solicitar capacidades externas desde expediente"),
    "evaluacion.accion.approve": ("Evaluación EIAAX", "Aprobar acciones externas de ejecución"),
    "evaluacion.indicadores.manage": ("Evaluación EIAAX", "Gestionar indicadores de impacto"),
    "gobierno.view": ("Gobierno operacional", "Consultar políticas y solicitudes de acción"),
    "gobierno.manage": ("Gobierno operacional", "Gestionar políticas de acción"),
    "gobierno.execute": ("Gobierno operacional", "Solicitar acciones operacionales"),
    "gobierno.approve": ("Gobierno operacional", "Aprobar o rechazar solicitudes"),
    "gobierno.visibility": ("Gobierno operacional", "Gestionar visibilidad generalizada"),
    "gobierno.ia_policy": ("Gobierno operacional", "Gestionar políticas de gobierno IA"),
    "gobierno.audit": ("Gobierno operacional", "Consultar eventos de gobierno operacional"),
    "gobierno.confianza.view": ("Gobierno operacional", "Ver Centro de Confianza"),
    "gobierno.clasificacion.view": ("Gobierno operacional", "Consultar clasificación de información"),
    "gobierno.clasificacion.assign": ("Gobierno operacional", "Asignar clasificación a objetos"),
    "gobierno.trazabilidad.view": ("Gobierno operacional", "Consultar trazabilidad empresarial"),
    "gobierno.evidencia.view": ("Gobierno operacional", "Consultar evidencia vinculada"),
    "gobierno.evidencia.link": ("Gobierno operacional", "Vincular evidencia a decisiones"),
    "gobierno.auditoria.consulta": ("Gobierno operacional", "Consultar auditoría federada en español"),
    "negocio.view": ("Centro de Negocios", "Consultar oportunidades y propuestas comerciales"),
    "negocio.manage": ("Centro de Negocios", "Gestionar ciclo comercial y propuestas"),
    "negocio.economy.private": ("Centro de Negocios", "Ver economía privada en propuestas"),
    "negocio.proposal.approve": ("Centro de Negocios", "Aprobar propuestas y decidir precio"),
    "negocio.proposal.present": ("Centro de Negocios", "Presentar propuestas al cliente"),
    "negocio.contract": ("Centro de Negocios", "Contratar y convertir a implementación"),
    "continuidad_comercial.view": ("Continuidad comercial", "Ver continuidad contrato→resultado"),
    "continuidad_comercial.manage": ("Continuidad comercial", "Gestionar cambios de alcance"),
    "continuidad_comercial.close": ("Continuidad comercial", "Cerrar contratos y offboarding"),
    "transformacion.view": ("Transformación", "Consultar dossier y diagnóstico adaptativo"),
    "transformacion.manage": ("Transformación", "Registrar necesidades y gestionar dossier"),
    "transformacion.execute": ("Transformación", "Ejecutar diagnóstico y motor de transformación"),
    "strategic_control.view": ("Centro Estratégico", "Ver cockpit estratégico de empresa/dossier"),
    "strategic_control.economia_privada": ("Centro Estratégico", "Ver economía privada interna (no publicable a entidad)"),
    "flujo_comercial.view": ("Flujo comercial", "Ver flujo prospecto→contratación"),
    "flujo_comercial.manage": ("Flujo comercial", "Gestionar presentación, instrumentos y garantías"),
    "espacio_externo.manage": ("Espacio externo", "Gestionar entidades empresa/prospecto/cliente"),
    "espacio_externo.publish": ("Espacio externo", "Publicar contenido a empresa"),
    "espacio_externo.acceso": ("Espacio externo", "Invitar y revocar accesos externos"),
    "espacio_externo.portal": ("Espacio externo", "Acceder al portal mi-espacio"),
    "espacio_externo.entregar": ("Espacio externo", "Entregar información solicitada"),
    "resultados.view": ("Inteligencia de resultados", "Consultar indicadores e informes de impacto"),
    "resultados.manage": ("Inteligencia de resultados", "Gestionar indicadores y plan de mejoramiento"),
    "resultados.validate": ("Inteligencia de resultados", "Registrar mediciones REAL con evidencia"),
    "resultados.informe.generate": ("Inteligencia de resultados", "Generar informes de impacto"),
    "partners.view": ("Partners", "Consultar partners y aliados comerciales"),
    "partners.manage": ("Partners", "Crear y administrar partners"),
    "partners.org.grant": ("Partners", "Asociar organizaciones a partners"),
    "partners.user.assign": ("Partners", "Asignar usuarios a partners"),
    "partners.audit": ("Partners", "Consultar auditoría de partners"),
    "inteligencia_empresarial.view": ("Inteligencia Empresarial", "Ver panorama adaptativo, suficiencia y cadena analítica"),
    "inteligencia_empresarial.manage": ("Inteligencia Empresarial", "Ejecutar evaluación adaptativa y registrar evidencia proactiva"),
    "inteligencia_externa.view": ("Inteligencia externa", "Consultar fuentes y señales externas"),
    "inteligencia_externa.manage": ("Inteligencia externa", "Administrar fuentes externas"),
    "inteligencia_externa.ingest": ("Inteligencia externa", "Registrar señales externas"),
    "inteligencia_externa.validate": ("Inteligencia externa", "Validar análisis externo"),
    "datos.view": ("Gobierno de datos", "Consultar catálogo y políticas"),
    "datos.classify": ("Gobierno de datos", "Clasificar y catalogar datos"),
    "datos.manage_policy": ("Gobierno de datos", "Gestionar políticas de datos"),
    "datos.export": ("Gobierno de datos", "Registrar exportaciones"),
    "datos.audit": ("Gobierno de datos", "Auditar accesos y hallazgos"),
    "datos.requests": ("Gobierno de datos", "Gestionar solicitudes sobre datos"),
    "datos.retention": ("Gobierno de datos", "Gestionar retención y legal hold"),
    "integraciones.view": ("Integraciones", "Consultar conectores e historial"),
    "integraciones.create": ("Integraciones", "Crear conectores"),
    "integraciones.configure": ("Integraciones", "Configurar conectores y mapeos"),
    "integraciones.test": ("Integraciones", "Probar conexión de conectores"),
    "integraciones.execute": ("Integraciones", "Ejecutar conectores"),
    "integraciones.manage_secrets": ("Integraciones", "Gestionar referencias de credenciales"),
    "aprendizaje.view": ("Aprendizaje", "Consultar ciclos y patrones de aprendizaje"),
    "aprendizaje.evaluate": ("Aprendizaje", "Evaluar ciclos y registrar retroalimentación"),
    "aprendizaje.recalibrate": ("Aprendizaje", "Aplicar recalibraciones aprobadas"),
    "aprendizaje.approve": ("Aprendizaje", "Aprobar o rechazar recalibraciones"),
    "optimizacion.view": ("Optimización", "Consultar recomendaciones y simulaciones"),
    "optimizacion.simulate": ("Optimización", "Ejecutar simulaciones de portafolio"),
    "optimizacion.create": ("Optimización", "Crear y recalcular recomendaciones"),
    "optimizacion.approve": ("Optimización", "Aprobar o rechazar recomendaciones"),
    "optimizacion.execute": ("Optimización", "Ejecutar recomendaciones aprobadas"),
    "optimizacion.configure": ("Optimización", "Configurar pesos y objetivos"),
    "comercial.view": ("Comercial", "Consultar propuestas y planes comerciales"),
    "comercial.simulate": ("Comercial", "Simular valor y precio"),
    "comercial.create": ("Comercial", "Crear y editar propuestas comerciales"),
    "comercial.approve": ("Comercial", "Aprobar precio final y propuestas"),
    "comercial.manage_plans": ("Comercial", "Administrar planes comerciales"),
    "tco.view": ("TCO", "Consultar costo total y tablero"),
    "tco.manage": ("TCO", "Gestionar costos y distribuciones"),
    "tco.simulate": ("TCO", "Simular escenarios de costo"),
    "proveedores.view": ("Proveedores", "Consultar proveedores y aliados"),
    "proveedores.manage": ("Proveedores", "Administrar proveedores, tarifas y contratos"),
    "alianzas.view": ("Alianzas", "Consultar alianzas estratégicas"),
    "alianzas.manage": ("Alianzas", "Gestionar alianzas estratégicas"),
    "implementacion.view": ("Implementación", "Consultar proyectos de implementación"),
    "implementacion.manage": ("Implementación", "Gestionar implementación y pilotos"),
    "implementacion.approve_go_live": ("Implementación", "Aprobar salida a producción"),
    "exito_cliente.view": ("Éxito del cliente", "Consultar planes de éxito y salud"),
    "exito_cliente.manage": ("Éxito del cliente", "Gestionar adopción y objetivos"),
    "exito_cliente.review": ("Éxito del cliente", "Realizar revisiones periódicas"),
    "segmentacion.view": ("Segmentación", "Consultar segmentos y perfiles comerciales"),
    "segmentacion.manage": ("Segmentación", "Administrar segmentación y perfiles"),
    "planes.view": ("Planes", "Consultar catálogo de planes y paquetes"),
    "planes.manage": ("Planes", "Administrar planes, paquetes y versiones"),
    "planes.recommend": ("Planes", "Generar recomendaciones de plan"),
    "planes.approve_discount": ("Planes", "Aprobar descuentos comerciales"),
    "platform.organization.view": ("Plataforma", "Ver empresas de la plataforma"),
    "platform.organization.create": ("Plataforma", "Crear empresas"),
    "platform.organization.manage": ("Plataforma", "Activar o desactivar empresas"),
    "control_center.view": ("Centro de Control", "Ver centro de control ejecutivo"),
    "continuidad.view": ("Continuidad", "Consultar continuidad operativa y resiliencia"),
    "continuidad.manage": ("Continuidad", "Administrar servicios críticos y planes"),
    "continuidad.activate": ("Continuidad", "Activar planes de contingencia"),
    "continuidad.test": ("Continuidad", "Ejecutar pruebas de continuidad y restauración"),
    "incidentes.view": ("Incidentes", "Consultar incidentes operativos"),
    "incidentes.manage": ("Incidentes", "Gestionar incidentes operativos"),
    "incidentes.close": ("Incidentes", "Cerrar incidentes operativos"),
    "backups.view": ("Respaldos", "Consultar políticas y ejecuciones de respaldo"),
    "backups.manage": ("Respaldos", "Administrar políticas y registrar ejecuciones"),
    "backups.verify": ("Respaldos", "Verificar integridad de respaldos"),
    "support.view": ("Soporte", "Ver casos de mesa de ayuda"),
    "support.create": ("Soporte", "Crear casos de soporte"),
    "support.assign": ("Soporte", "Asignar casos de soporte"),
    "support.update": ("Soporte", "Actualizar casos de soporte"),
    "support.resolve": ("Soporte", "Resolver casos de soporte"),
    "support.close": ("Soporte", "Cerrar casos de soporte"),
    "support.admin": ("Soporte", "Administrar mesa de ayuda y SLA"),
}

SYSTEM_ROLE_CODES = {"admin", "operator", "viewer", "superadmin", "external_prospect"}

PROTECTED_ASSIGNMENT_ROLE_CODES = {"superadmin", "platform_admin", "SUPERADMIN"}

# Referencia estática para seed/tests — NO usar como fuente runtime de permisos.
ROLE_PERMISSIONS_FALLBACK: dict[str, set[str]] = {
    "admin": (
        EMPLOYEE_PERMISSIONS
        | NOTIFICATION_PERMISSIONS
        | COMMUNICATIONS_PERMISSIONS
        | ADMIN_PERMISSIONS
        | OPERATIONS_PERMISSIONS
        | AUTOMATION_PERMISSIONS
        | AUDIT_PERMISSIONS
        | CAPABILITY_PERMISSIONS
        | TOOL_PERMISSIONS
        | KNOWLEDGE_PERMISSIONS
        | TEST_LAB_PERMISSIONS
        | FINOPS_PERMISSIONS
        | FINOPS_ECONOMY_PRIVATE_PERMISSIONS
        | LLM_PERMISSIONS
        | SALUD_PERMISSIONS
        | OPORTUNIDADES_PERMISSIONS
        | LINEA_BASE_PERMISSIONS
        | VALORACION_PERMISSIONS
        | DIAGNOSTICOS_PERMISSIONS
        | EVALUACION_PERMISSIONS
        | PARTNER_PERMISSIONS
        | GOBIERNO_OPERACIONAL_PERMISSIONS
        | NEGOCIO_PERMISSIONS
        | CONTINUIDAD_COMERCIAL_PERMISSIONS
        | TRANSFORMACION_PERMISSIONS
        | STRATEGIC_CONTROL_PERMISSIONS
        | FLUJO_COMERCIAL_PERMISSIONS
        | ESPACIO_EXTERNO_PERMISSIONS
        | RESULTADOS_PERMISSIONS
        | INTELIGENCIA_EMPRESARIAL_PERMISSIONS
        | INTELIGENCIA_EXTERNA_PERMISSIONS
        | CONTROL_CENTER_PERMISSIONS
        | CONTINUIDAD_PERMISSIONS
        | INCIDENTES_PERMISSIONS
        | BACKUPS_PERMISSIONS
        | SUPPORT_PERMISSIONS
        | DATOS_PERMISSIONS
        | INTEGRATION_PERMISSIONS
        | APRENDIZAJE_PERMISSIONS
        | OPTIMIZACION_PERMISSIONS
        | SECURITY_PERMISSIONS
        | IDENTITY_PERMISSIONS
        | COMMERCIAL_PERMISSIONS
        | TCO_PERMISSIONS
        | IMPLEMENTACION_PERMISSIONS
        | SEGMENTATION_PERMISSIONS
        | EMPLOYEE_AUDIT_PERMISSIONS
    ),
    "superadmin": (
        EMPLOYEE_PERMISSIONS
        | NOTIFICATION_PERMISSIONS
        | COMMUNICATIONS_PERMISSIONS
        | ADMIN_PERMISSIONS
        | OPERATIONS_PERMISSIONS
        | AUTOMATION_PERMISSIONS
        | AUDIT_PERMISSIONS
        | CAPABILITY_PERMISSIONS
        | TOOL_PERMISSIONS
        | KNOWLEDGE_PERMISSIONS
        | TEST_LAB_PERMISSIONS
        | FINOPS_PERMISSIONS
        | FINOPS_ECONOMY_PRIVATE_PERMISSIONS
        | LLM_PERMISSIONS
        | SALUD_PERMISSIONS
        | OPORTUNIDADES_PERMISSIONS
        | LINEA_BASE_PERMISSIONS
        | VALORACION_PERMISSIONS
        | DIAGNOSTICOS_PERMISSIONS
        | EVALUACION_PERMISSIONS
        | PARTNER_PERMISSIONS
        | GOBIERNO_OPERACIONAL_PERMISSIONS
        | NEGOCIO_PERMISSIONS
        | CONTINUIDAD_COMERCIAL_PERMISSIONS
        | TRANSFORMACION_PERMISSIONS
        | STRATEGIC_CONTROL_PERMISSIONS
        | FLUJO_COMERCIAL_PERMISSIONS
        | ESPACIO_EXTERNO_PERMISSIONS
        | RESULTADOS_PERMISSIONS
        | INTELIGENCIA_EMPRESARIAL_PERMISSIONS
        | INTELIGENCIA_EXTERNA_PERMISSIONS
        | CONTROL_CENTER_PERMISSIONS
        | CONTINUIDAD_PERMISSIONS
        | INCIDENTES_PERMISSIONS
        | BACKUPS_PERMISSIONS
        | SUPPORT_PERMISSIONS
        | DATOS_PERMISSIONS
        | INTEGRATION_PERMISSIONS
        | APRENDIZAJE_PERMISSIONS
        | OPTIMIZACION_PERMISSIONS
        | COMMERCIAL_PERMISSIONS
        | TCO_PERMISSIONS
        | IMPLEMENTACION_PERMISSIONS
        | SEGMENTATION_PERMISSIONS
        | PLATFORM_PERMISSIONS
        | SECURITY_PERMISSIONS
        | IDENTITY_PERMISSIONS
        | EMPLOYEE_AUDIT_PERMISSIONS
    ),
    "operator": {
        "employee.view",
        "employee.create",
        "employee.edit",
        "employee.test",
        "auditor_empleados.view",
        "auditor_empleados.execute",
        "notification.acknowledge",
        "alert_rule.view",
        "communications.view",
        "communications.send",
        "communications.schedule",
        "communications.history.view",
        "operations.view",
        "operations.execute",
        "operations.manage",
        "operations.cancel",
        "operations.reassign",
        "operations.approve",
        "automation.view",
        "automation.create",
        "automation.edit",
        "automation.activate",
        "automation.pause",
        "automation.run",
        "automation.view_runs",
        "audit.view",
        "admin.organization.view",
        "admin.config.view",
        "capability.view",
        "tool.view",
        "knowledge.view",
        "knowledge.manage",
        "knowledge.upload",
        "knowledge.use",
        "test_lab.view",
        "test_lab.run",
        "finops.view",
        "finops.manage",
        "finops.budget",
        "llm.view",
        "llm.manage",
        "llm.use",
        "salud.cargar_datos",
        "salud.ejecutar_analisis",
        "salud.consultar_diagnostico",
        "salud.aceptar_recomendaciones",
        "oportunidades.view",
        "oportunidades.manage",
        "oportunidades.evaluate",
        "oportunidades.approve",
        "oportunidades.activate",
        "linea_base.view",
        "linea_base.manage",
        "linea_base.validate",
        "valoracion.view",
        "valoracion.manage",
        "valoracion.validate",
        "valoracion.roi",
        "diagnosticos.view",
        "diagnosticos.generate",
        "diagnosticos.validate",
        "evaluacion.view",
        "evaluacion.manage",
        "evaluacion.evaluate",
        "evaluacion.visibility",
        "evaluacion.vista_entidad",
        "evaluacion.accion.request",
        "evaluacion.accion.approve",
        "evaluacion.indicadores.manage",
        "inteligencia_externa.view",
        "inteligencia_externa.manage",
        "inteligencia_externa.ingest",
        "inteligencia_externa.validate",
        "control_center.view",
        "continuidad.view",
        "continuidad.manage",
        "continuidad.activate",
        "continuidad.test",
        "incidentes.view",
        "incidentes.manage",
        "incidentes.close",
        "backups.view",
        "backups.manage",
        "backups.verify",
        "datos.view",
        "datos.classify",
        "datos.manage_policy",
        "datos.export",
        "datos.audit",
        "datos.requests",
        "datos.retention",
        "integraciones.view",
        "integraciones.create",
        "integraciones.configure",
        "integraciones.test",
        "integraciones.execute",
        "aprendizaje.view",
        "aprendizaje.evaluate",
        "aprendizaje.recalibrate",
        "optimizacion.view",
        "optimizacion.simulate",
        "optimizacion.create",
        "comercial.view",
        "comercial.simulate",
        "comercial.create",
        "tco.view",
        "tco.manage",
        "tco.simulate",
        "proveedores.view",
        "proveedores.manage",
        "alianzas.view",
        "implementacion.view",
        "implementacion.manage",
        "exito_cliente.view",
        "exito_cliente.manage",
        "segmentacion.view",
        "segmentacion.manage",
        "planes.view",
        "planes.manage",
        "planes.recommend",
        "support.view",
        "support.create",
        "support.assign",
        "support.update",
        "support.resolve",
        "support.close",
        "gobierno.view",
        "gobierno.execute",
        "gobierno.approve",
        "gobierno.visibility",
        "gobierno.ia_policy",
        "gobierno.audit",
        "gobierno.confianza.view",
        "gobierno.clasificacion.view",
        "gobierno.trazabilidad.view",
        "negocio.view",
        "continuidad_comercial.view",
        "transformacion.view",
        "transformacion.manage",
        "transformacion.execute",
        "strategic_control.view",
        "strategic_control.economia_privada",
        "flujo_comercial.view",
        "flujo_comercial.manage",
        "espacio_externo.manage",
        "espacio_externo.publish",
        "espacio_externo.acceso",
        "resultados.view",
        "partners.view",
    },
    "viewer": {
        "employee.view",
        "notification.view",
        "operations.view",
        "automation.view",
        "automation.view_runs",
        "audit.view",
        "admin.organization.view",
        "capability.view",
        "tool.view",
        "knowledge.view",
        "knowledge.use",
        "test_lab.view",
        "finops.view",
        "salud.consultar_diagnostico",
        "oportunidades.view",
        "linea_base.view",
        "valoracion.view",
        "valoracion.roi",
        "diagnosticos.view",
        "inteligencia_externa.view",
        "control_center.view",
        "continuidad.view",
        "incidentes.view",
        "backups.view",
        "datos.view",
        "integraciones.view",
        "aprendizaje.view",
        "optimizacion.view",
        "comercial.view",
        "comercial.simulate",
        "tco.view",
        "tco.simulate",
        "proveedores.view",
        "alianzas.view",
        "implementacion.view",
        "exito_cliente.view",
        "segmentacion.view",
        "planes.view",
        "support.view",
        "support.create",
        "gobierno.view",
        "gobierno.confianza.view",
        "gobierno.clasificacion.view",
        "gobierno.trazabilidad.view",
        "transformacion.view",
        "strategic_control.view",
        "resultados.view",
        "partners.view",
    },
    "external_prospect": {
        "espacio_externo.portal",
        "espacio_externo.entregar",
    },
}


def is_canonical_active_value(raw) -> bool:
    """Solo valores canónicos persistidos equivalen a ACTIVE."""
    return raw is True or raw == 1


def read_role_is_active_raw(db: Session, role_id: str):
    return db.execute(
        text("SELECT is_active FROM roles WHERE id = :role_id"),
        {"role_id": role_id},
    ).scalar()


def is_role_strictly_active(role: Role, db: Session | None = None) -> bool:
    """Validación estricta desde valor persistido — corrupción SQLite → DENY."""
    if db is not None and role.id:
        return is_canonical_active_value(read_role_is_active_raw(db, role.id))
    return is_canonical_active_value(role.is_active)


def find_role_candidates_for_user(db: Session, user: User) -> list[Role]:
    role_code = (user.role or "").strip()
    if not role_code:
        return []
    return (
        db.query(Role)
        .filter(
            Role.code == role_code,
            (Role.organization_id == user.organization_id) | (Role.organization_id.is_(None)),
        )
        .order_by(Role.organization_id.is_(None).asc(), Role.created_at.asc())
        .all()
    )


def find_role_candidates_for_code(db: Session, role_code: str, org_id: str) -> list[Role]:
    code = (role_code or "").strip()
    if not code:
        return []
    return (
        db.query(Role)
        .filter(
            Role.code == code,
            (Role.organization_id == org_id) | (Role.organization_id.is_(None)),
        )
        .order_by(Role.organization_id.is_(None).asc(), Role.created_at.asc())
        .all()
    )


def resolve_authoritative_role(db: Session, user: User) -> Role | None:
    """Resuelve un único rol autoritativo o None (ambigüedad/inactivo → DENY)."""
    candidates = find_role_candidates_for_user(db, user)
    if not candidates:
        return None

    org_roles = [r for r in candidates if r.organization_id == user.organization_id]
    if org_roles:
        if len(org_roles) > 1:
            logger.warning("roles_ambiguous org=%s code=%s count=%s", user.organization_id, user.role, len(org_roles))
            return None
        role = org_roles[0]
        return role if is_role_strictly_active(role, db) else None

    global_roles = [r for r in candidates if r.organization_id is None]
    if len(global_roles) != 1:
        logger.warning("roles_ambiguous_global code=%s count=%s", user.role, len(global_roles))
        return None
    role = global_roles[0]
    return role if is_role_strictly_active(role, db) else None


def resolve_role_for_assignable(db: Session, role_code: str, org_id: str) -> Role | None:
    candidates = find_role_candidates_for_code(db, role_code, org_id)
    if not candidates:
        return None
    org_roles = [r for r in candidates if r.organization_id == org_id]
    if org_roles:
        if len(org_roles) > 1:
            return None
        role = org_roles[0]
        return role if is_role_strictly_active(role, db) else None
    global_roles = [r for r in candidates if r.organization_id is None]
    if len(global_roles) != 1:
        return None
    role = global_roles[0]
    return role if is_role_strictly_active(role, db) else None


def find_role_record_for_user(db: Session, user: User) -> Role | None:
    """Compat: registro de rol sin validar activo (usar resolve_authoritative_role en runtime)."""
    candidates = find_role_candidates_for_user(db, user)
    if not candidates:
        return None
    org_roles = [r for r in candidates if r.organization_id == user.organization_id]
    if org_roles:
        return org_roles[0] if len(org_roles) == 1 else None
    global_roles = [r for r in candidates if r.organization_id is None]
    return global_roles[0] if len(global_roles) == 1 else None


def resolve_role_for_user(db: Session, user: User) -> Role | None:
    return resolve_authoritative_role(db, user)


def role_permission_codes(db: Session, role: Role) -> set[str]:
    rows = (
        db.query(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .filter(RolePermission.role_id == role.id)
        .all()
    )
    return {row[0] for row in rows}


def user_permissions(user: User, db: Session | None = None) -> set[str]:
    """DENY BY DEFAULT — permisos solo desde rol autoritativo en BD."""
    if db is None:
        return set()
    try:
        role = resolve_authoritative_role(db, user)
        if role is None:
            return set()
        return role_permission_codes(db, role)
    except Exception:
        logger.exception("role_permission_resolution_failed user=%s", user.id)
        return set()


def assert_permission_subset(actor: User, requested: set[str], db: Session, *, action: str) -> None:
    allowed = user_permissions(actor, db)
    extra = requested - allowed
    if extra:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No puede {action}: permisos no autorizados ({', '.join(sorted(extra))})",
        )


def assert_role_assignable(actor: User, role_code: str, org_id: str, db: Session) -> None:
    normalized = role_code.strip().lower()
    if normalized in PROTECTED_ASSIGNMENT_ROLE_CODES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Rol de plataforma no asignable")
    role = resolve_role_for_assignable(db, role_code, org_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Rol no válido para la organización")
    if role.organization_id and role.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Rol de otra organización")
    assert_permission_subset(actor, role_permission_codes(db, role), db, action="asignar rol")


def check_permission(user: User, permission: str, db: Session | None = None) -> None:
    if permission not in user_permissions(user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para realizar esta acción.",
        )


def require_permission(permission: str):
    def checker(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        check_permission(user, permission, db)
        return user

    return checker


def is_system_role(code: str) -> bool:
    return code in SYSTEM_ROLE_CODES
