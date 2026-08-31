import { canAccessRoute } from "../auth/permissions";
import { MENU } from "./menu";

/** Rutas excluidas como destino home (ajustes personales, no modulos operativos). */
export const HOME_ROUTE_EXCLUDE = new Set<string>(["/mi-seguridad"]);

/** Orden estable de rutas navegables derivado del menu lateral. */
export function getNavRoutesInOrder(): string[] {
  const seen = new Set<string>();
  const ordered: string[] = [];
  for (const section of MENU) {
    for (const item of section.items) {
      if (item.to === "#" || seen.has(item.to)) {
        continue;
      }
      seen.add(item.to);
      ordered.push(item.to);
    }
  }
  return ordered;
}

/**
 * Primera ruta funcional accesible segun permisos efectivos.
 * Retorna "/" si el usuario tiene control_center.view.
 * Retorna null si no hay modulo operativo habilitado.
 */
export function resolveHomeRoute(permissions: Set<string>): string | null {
  for (const path of getNavRoutesInOrder()) {
    if (HOME_ROUTE_EXCLUDE.has(path)) {
      continue;
    }
    if (canAccessRoute(path, permissions)) {
      return path;
    }
  }
  return null;
}
