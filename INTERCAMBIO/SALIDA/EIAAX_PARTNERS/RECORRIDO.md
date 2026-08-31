# Recorrido operativo

## 1. Crear partner

`POST /api/partners` → estado BORRADOR, código auto PTR-NNNN.

UI: Partners → Nuevo partner → formulario.

## 2. Activar / desactivar

`POST /api/partners/{id}/estado` con `{"estado": "ACTIVO"}` o `INACTIVO`.

UI: Detalle → Activar / Desactivar.

## 3. Asociar organización

`POST /api/partners/{id}/organizaciones` con `organization_id` y `alcance`.

UI: Pestaña Organizaciones → selector + checkboxes de alcance.

## 4. Asignar usuario

`POST /api/partners/{id}/usuarios` con `user_id` y `rol`.

UI: Pestaña Usuarios → ID usuario + rol.

## 5. Conceder / ajustar alcance

- Al crear grant: alcance inicial
- `PATCH /api/partners/{id}/organizaciones/{grant_id}/alcance`

UI: Pestaña Alcance → checkboxes por organización.

## 6. Revocar

- Org: `POST .../organizaciones/{grant_id}/revocar`
- Usuario: `POST .../usuarios/{membership_id}/revocar`

## 7. Auditar

`GET /api/partners/{id}/auditoria`

UI: Pestaña Actividad.

## 8. Consultar contexto organización (partner user)

`GET /api/partners/{id}/organizaciones/{org_id}/contexto`

Retorna datos filtrados según alcance (CC, trabajo, etc.).
