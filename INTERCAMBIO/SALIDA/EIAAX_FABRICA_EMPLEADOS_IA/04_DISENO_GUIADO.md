# 04 — Diseño guiado

## Experiencia (español)

Recorrido existente en `EmployeeWizardPage.tsx`:

1. **Propósito** — ¿Qué hará? ¿Por qué?
2. **Responsabilidades** — Rol y objetivo
3. **Conocimiento** — Fuentes autorizadas
4. **Capacidades** — Herramientas y permisos
5. **Autonomía** — Nivel y supervisión
6. **Modelo/costo** — Política de modelo y límites
7. **Prueba** — Casos controlados
8. **Aprobación** — Si aplica por riesgo
9. **Publicación** — Separada de guardar

## Biblioteca

`DirectoryPage.tsx` renombrada conceptualmente a **Biblioteca de Empleados IA**:

- Búsqueda y filtro por estado
- Distingue plantilla (`is_template`) vs instancia
- Clon como borrador vía API

## Puente desde Arquitecto

`ArquitectoTransformacionPage.tsx`:

- Lista requerimientos pendientes (`GET /api/transformacion/requerimientos-empleado-ia`)
- Botón **Crear borrador en Fábrica** — prellena sin re-solicitar datos del dossier

## Principios UX

- No formulario técnico interminable: plantillas aceleran configuración
- Preguntas de negocio visibles en español
- Guardar ≠ publicar ≠ activar
