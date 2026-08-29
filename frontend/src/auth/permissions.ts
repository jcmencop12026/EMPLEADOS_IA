/** Permisos mínimos por ruta de navegación — alineado con RBAC backend 840B. */
export const ROUTE_PERMISSIONS: Record<string, string[]> = {
  "/": ["control_center.view"],
  "/operaciones": ["operations.view"],
  "/operaciones/solicitud": ["operations.execute"],
  "/ejecuciones": ["operations.view"],
  "/aprobaciones": ["operations.view", "operations.approve"],
  "/automatizaciones": ["automation.view"],
  "/salud/diagnostico": ["salud.consultar_diagnostico"],
  "/directorio": ["employee.view"],
  "/empleados/nuevo": ["employee.create"],
  "/capacidades": ["capability.view"],
  "/herramientas": ["tool.view"],
  "/conocimiento": ["knowledge.view"],
  "/test-lab": ["test_lab.view"],
  "/lineas-base": ["linea_base.view"],
  "/comercial": ["comercial.view"],
  "/tco": ["tco.view"],
  "/oportunidades": ["oportunidades.view"],
  "/senales": ["oportunidades.view"],
  "/diagnosticos": ["diagnosticos.view"],
  "/inteligencia-externa": ["inteligencia_externa.view"],
  "/costos-valor": ["finops.view"],
  "/notificaciones": ["notification.view"],
  "/auditoria": ["audit.view"],
  "/administracion/empresas": ["platform.organization.view"],
  "/administracion/usuarios": ["admin.user.view"],
  "/administracion/roles": ["admin.role.view"],
  "/administracion/organizacion": ["admin.organization.view"],
  "/administracion/configuracion": ["admin.config.view"],
  "/administracion/proveedores-ia": ["llm.view"],
  "/administracion/seguridad": ["admin.security.view"],
};

export function canAccessRoute(path: string, permissions: Set<string>): boolean {
  const required = ROUTE_PERMISSIONS[path];
  if (!required || required.length === 0) {
    return true;
  }
  return required.some((code) => permissions.has(code));
}

export function filterMenuByPermissions<T extends { to: string }>(
  items: T[],
  permissions: Set<string>,
): T[] {
  return items.filter((item) => canAccessRoute(item.to, permissions));
}
