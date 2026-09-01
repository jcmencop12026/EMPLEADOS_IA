# 12 — Guía visual

## Recorrido sugerido (español)

### Biblioteca
**Menú → Directorio / Biblioteca de Empleados IA**
- Ver empleados por estado
- Filtrar y buscar
- Acceder a detalle

### Crear desde cero
**Biblioteca → Nuevo empleado → Wizard**
1. Propósito y plantilla
2. Responsabilidades
3. Conocimiento autorizado
4. Capacidades y herramientas
5. Autonomía y límites
6. Modelo IA
7. Prueba controlada
8. Aprobación (si aplica)
9. Publicar y activar

### Crear desde Arquitecto
**Arquitecto de Transformación → Requerimientos Empleado IA**
- Ver requerimientos pendientes
- **Crear borrador en Fábrica**
- Continuar en wizard/detalle

### Operación
**Detalle del empleado**
- Pestañas: configuración, pruebas, aprobaciones, métricas
- Acciones: pausar, retirar, clonar

## Componentes tocados

| Componente | Cambio |
|------------|--------|
| `DirectoryPage.tsx` | Título Biblioteca |
| `ArquitectoTransformacionPage.tsx` | Puente requerimientos |
| `api.ts` | Funciones biblioteca, clone, estimate, validate |
| `EmployeeWizardPage.tsx` | Sin cambio estructural (reutilizado) |
| `EmployeeDetailPage.tsx` | Sin cambio estructural (reutilizado) |

GENERAL integrará sistema visual transversal posteriormente.
