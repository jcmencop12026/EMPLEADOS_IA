# CODEX — Doble auditoría independiente

Fecha: 2026-08-24

Alcance: PR #6 CURSOR-810B y PR #9 CURSOR-840. No se realizó merge, corrección, push, rebase ni cherry-pick.

## PR #6 — CURSOR-810B — Automatizaciones V1

### Identidad y aislamiento

- HEAD MAIN: `b887a2e77c646a5b0c82d47837dfaaaed9c491ce`
- HEAD PR: `b1a5c7fb103c90f6ab6cb98496601ef9b93a2177`
- Merge-base: coincide exactamente con HEAD MAIN.
- DIFF: 23 archivos, 3.203 inserciones, 5 eliminaciones.
- SCOPE ISOLATION: correcto para 810; sólo código/tests de automatizaciones y dos informes Cursor. No incorpora 820, 830 o 840.
- 805 PRESERVED: sí. No hay archivos eliminados, `.gitignore` no cambia y `main.py` conserva startup/reparación 805 con adiciones para 810.

### Backend y ejecución

- MODELS: presentes (`Automation`, `AutomationRun`) con unique `(automation_id, occurrence_key)`.
- MIGRATION: revisión estática correcta, `down_revision=5b2eb2437398`; no se reprodujo ciclo Alembic independiente.
- RECURRENCE: ONE_TIME, DAILY, WEEKLY, MONTHLY e INTERVAL cubiertos; pruebas de `start_at` futuro pasan.
- TIMEZONE: America/Bogota y cambios de fecha cubiertos por suite; sin fallo reproducido naive/aware.
- IDEMPOTENCY: correcta para ocurrencia con clave estable, **falla para redelivery de INTERNAL_EVENT**.
- SCHEDULER: recorrido real cubierto en single-worker.
- RESTART / MISSED RUN: cubiertos parcialmente por suite; restart no tuvo prueba multiproceso real.
- MULTI-WORKER: pendiente B. Lectura y ejecución no usan claim/lease atómico; unique reduce duplicado de una ocurrencia del scheduler, pero max-runs/day también tiene carrera.
- ORCHESTRATOR E2E: recorridos RUN NOW, scheduler e internal event pasan pruebas funcionales.
- RUN NOW: pasa.
- RETRIES: semántica N+1 correcta para 0/1/4/10, pero el retardo configurado falla.
- TIMEOUT: **falla A**.
- APPROVAL: flujo real crea WorkPlan/ApprovalRequest, espera, continúa tras aprobar y no ejecuta tras rechazo; pasa.
- FINOPS: **pendiente B**. El pre-check confía en `workflow.estimated_cost` suministrado por usuario; puede omitirse o subestimarse. No es estimación preventiva fiable.
- TENANT: create/update/pre-execution revalidan empleado y organización; pasa para rutas revisadas.
- PERMISSIONS: protección backend presente para rutas revisadas.
- AUDIT: **incompleto**; faltan acciones exactas scheduled, internal_event, timeout, approved y rejected.
- INTERNAL EVENT: integración real event bus → subscriber → automation → run → WorkPlan existe; anti-loop existe, pero replay no es idempotente.

### UI

- UI/CRUD: crear, estados, run-now e historial existen; edición es destructiva para campos no recargados.
- WIZARD: español y navegación existen. Empleado no es obligatorio; INTERNAL_EVENT no permite definir `event_type` desde UI.
- MONITOR: muestra estado, fechas, intentos, coste y WorkPlan; trigger/drill-down son parciales.
- Recorrido visual autenticado no se ejecutó; evaluación UI se hizo por código y build.

### Defectos A

1. **Timeout no detiene el trabajo real** — `backend/app/services/automation_service.py:394-402`. `future.result(timeout=...)` vence, pero el `ThreadPoolExecutor` usado como context manager espera al worker en `__exit__`; no existe cancelación de una herramienta ya iniciada. Puede continuar y producir efectos después de marcar fallo.
2. **Replay de INTERNAL_EVENT duplica ejecuciones** — `automation_service.py:489-490,712-740`. Se descarta identidad estable del evento y `occurrence_key` se deriva del reloj. La misma entrega repetida crea otro run.
3. **`retry_delay_seconds` no se respeta** — `automation_service.py:644-645`. El código duerme `min(retry_delay_seconds, 1)` y reduce cualquier retardo mayor de un segundo.
4. **Editar sobrescribe controles persistidos** — `frontend/src/pages/AutomationWizardPage.tsx:78-145`. No recarga start_at, recurrencia detallada, retries, delay, timeout ni FinOps; luego envía defaults y `max_runs_per_day=10`.

### Pendientes

- A: los cuatro defectos anteriores.
- B: FinOps no usa estimación fiable; auditoría incompleta; carrera multi-worker/max-runs; registro duplicable de subscriber; monitor parcial.
- C: recorrido visual autenticado y ciclo Alembic independiente no ejecutados.

### Pruebas

- TESTS PASSED: 87
- TESTS FAILED: 0
- TESTS SKIPPED: 0
- Advertencias: 3
- Duración: 99,51 s
- NPM CI: correcto, 73 paquetes.
- NPM AUDIT: 0 vulnerabilidades.
- BUILD: correcto, Vite 6.4.3, 57 módulos.
- GIT: `git diff --check` limpio.
- Secretos/artefactos: no se encontraron patrones evidentes nuevos ni `.env`, DB, backups, logs o PID indebidos.

### Veredicto PR #6

**NO APTO PARA MERGE**

## PR #9 — CURSOR-840 — Administración V1

### Identidad y aislamiento

- HEAD MAIN: `b887a2e77c646a5b0c82d47837dfaaaed9c491ce`
- HEAD PR: `5c1e4b34ab3d49b5dae7a95376549050a39d1795`
- Merge-base: coincide exactamente con HEAD MAIN.
- DIFF: 24 archivos, 2.160 inserciones, 41 eliminaciones.
- SCOPE ISOLATION: correcto para 840; no incorpora 810/820/830 ni modifica infraestructura 805.

### Seguridad y backend

- SECURITY MODEL: modelos DB `Permission`, `Role`, `RolePermission` más fallback hardcoded.
- DUPLICATE AUTHORIZATION MODEL: **sí, dos fuentes efectivas incompatibles**. Un rol DB vacío recibe permisos del fallback.
- MODELS: presentes, pero `User.role` string y matriz DB/fallback forman autoridad híbrida.
- MIGRATION: **falla A en SQLite** y deja DDL parcial.
- USERS: listar/crear/actualizar/estado/reset existen. Username whitespace y email inválido son aceptados.
- PASSWORDS: bcrypt, no plaintext en modelo/respuestas generales/AuditLog. La contraseña temporal se devuelve deliberadamente sólo en reset. Falta prueba completa old-password/new-password.
- ROLES/PERMISSIONS: backend CRUD/asignación existe; faltan límites de delegación.
- ROLE MATRIX: sólo lectura en UI.
- REQUIRE_PERMISSION: backend devuelve 403 según permisos, pero la resolución híbrida concede fallback inesperado.
- TENANT/CROSS-TENANT: filtros por `organization_id` correctos para usuarios y roles auditados; intentos cross-tenant revisados son rechazados.
- PRIVILEGE ESCALATION: **falla A reproducida**.
- ORGANIZATION: GET/UPDATE tenant-scoped; UI tiene loading/error/empty.
- CONFIG: allowlist de cuatro claves, pero acepta idioma y formatos arbitrarios.
- TIMEZONE: `America/Bogota` aceptado; `America/Bogota_INVALID` rechazado 422.
- SECURITY PAGE: datos reales y error preservado; no convierte error a ceros.
- AUDIT: acciones principales existen, pero faltan `resource` y `resource_id` estructurados y consistentes; eventos de rol guardan sólo código.
- LANGUAGE: español predominante.
- ERROR HANDLING: parcial; acciones de estado/reset en usuarios carecen de `catch` visible.

### Defectos A

1. **Migración SQLite no instalable y no reintentable** — `backend/alembic/versions/a840c4d5e6f7_administration_840.py:33-34`. `op.create_foreign_key` sin batch mode lanza `NotImplementedError`; columnas previas quedan creadas, Alembic permanece en la revisión anterior y el reintento falla por columna duplicada.
2. **Autorización DB + fallback impide revocación total** — `backend/app/permissions.py:102-122`. Si el query DB no retorna códigos, cae a `ROLE_PERMISSIONS_FALLBACK`; reproducción: rol vacío obtuvo `employee.view`.
3. **Escalada de privilegios delegada** — `backend/app/services/admin_service.py:241-258` y `backend/app/routers/admin.py:67-82,161-179`. Un actor con permisos administrativos parciales creó rol, concedió `admin.security.view` que no poseía, se autoasignó el rol y accedió al panel: 201/200/200/200.
4. **UI no administra permisos personalizados** — `frontend/src/pages/admin/AdminRolesPage.tsx:30-59`. La matriz sólo muestra ✓/— y declara la edición para una iteración futura.

### Otros defectos y pendientes

- Username de espacios se crea como cadena vacía; email inválido también retorna 201.
- Email no tiene unique DB y admite duplicados.
- Idioma/formatos arbitrarios aceptados (por ejemplo `xx`, `DROP TABLE`, `99h`).
- AuditLog no satisface resource/resource_id estructurados para todos los eventos.
- UI usuarios carece de detalle, edición completa, bloqueo explícito, ordenamiento y confirmaciones; errores de algunas acciones no se capturan.
- La ruta de cambio de estado exige siempre `admin.user.activate`, incluso para desactivar, además del permiso de desactivar.

### Migración reproducida

1. `alembic upgrade 5b2eb2437398`: correcto.
2. Inserción de datos de control: correcta.
3. `alembic upgrade head`: falla con `No support for ALTER of constraints in SQLite dialect`.
4. `alembic current`: sigue en `5b2eb2437398`.
5. Reintento: `sqlite3.OperationalError: duplicate column name: status`.

### Pruebas

- TESTS PASSED: 62
- TESTS FAILED: 0
- TESTS SKIPPED: 0
- Advertencias: 2
- Duración: 86,09 s
- Nota: la suite usa `Base.metadata.create_all`, por eso no detecta la migración rota.
- NPM CI: correcto.
- NPM AUDIT: 0 vulnerabilidades.
- BUILD: correcto, 59 módulos; JS 272,44 kB (gzip 83,48 kB).
- GIT: `git diff --check` limpio.
- Secretos/artefactos: no se encontraron secretos productivos ni `.env`, DB, backups, logs o PID añadidos.

### Pendientes

- A: los cuatro defectos bloqueantes anteriores.
- B: validaciones username/email/config; contrato AuditLog; UI usuarios y manejo de errores; permiso de desactivación.
- C: recorrido visual autenticado completo no ejecutado; invalidación de contraseña anterior no comprobada E2E.

### Veredicto PR #9

**NO APTO PARA MERGE**

## Resumen consolidado

### PR #6 CURSOR-810B: NO APTO

Bloqueantes: timeout no efectivo; replay de eventos duplica trabajo; retry delay ignorado; edición del wizard sobrescribe configuración.

### PR #9 CURSOR-840: NO APTO

Bloqueantes: migración SQLite rota/parcial; autorización DB+fallback incompatible; escalada delegada reproducida; UI de permisos personalizada ausente.

**NO MERGE REALIZADO.**
