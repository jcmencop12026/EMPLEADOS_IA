# CURSOR 1350 — Gobierno de datos, privacidad y retención

## Identificación

| Campo | Valor |
|-------|-------|
| Bloque | 1350 |
| Rama | `cursor/1350-gobierno-datos-privacidad` |
| Base | `cursor/1250a-fix-aislamiento-tests` @ `6352836813da85e31514e19cef125bcff53b4191` |
| HEAD | `3cbc83b6813da85e31514e19cef125bcff53b4191` |
| Alembic head | `1350a1b2c3d4e` |

## Alcance implementado

Capa transversal funcional y auditable de gobierno de datos:

- Clasificación parametrizable (PUBLICO, INTERNO, CONFIDENCIAL, RESTRINGIDO + personalizadas)
- Categorías de información configurables
- Catálogo de datos con organización, fuente, retención, ambiente (PRODUCCIÓN/PRUEBA/SINTÉTICO)
- Linaje básico (FUENTE → INGESTA → TRANSFORMACIÓN → DESTINO → PROCESO)
- Uso por IA (LECTURA, ESCRITURA, EXPORTACIÓN, ENVÍO A PROVEEDOR, GENERACIÓN)
- Políticas de salida a proveedores IA (PERMITIDO / PROHIBIDO / PERMITIDO_CON_TRANSFORMACIÓN)
- Minimización (EXCLUIR, ENMASCARAR, PSEUDONIMIZAR, ANONIMIZAR)
- Retención y disposición (ELIMINAR, ANONIMIZAR, ARCHIVAR, REVISIÓN_MANUAL)
- Legal hold / bloqueo de eliminación
- Registro de accesos (sin contenido sensible completo)
- Propósitos autorizados y detección de uso fuera de propósito
- Autorizaciones / consentimiento genérico
- Solicitudes sobre datos (RECIBIDA → CERRADA)
- Control de exportaciones con aislamiento multiempresa
- Enmascaramiento básico (correo, teléfono, identificador, cuenta, texto)
- Secretos solo CONFIGURADO / NO CONFIGURADO
- Políticas por organización y globales obligatorias (SuperAdmin)
- Evaluación de riesgo explicable (BAJO → CRÍTICO)
- Hallazgos y acciones correctivas
- RBAC `datos.*`
- Adaptadores preparación 1270 y 1330 (sin integración)
- UI español: tablero, catálogo, clasificación, políticas, retención, accesos, solicitudes, hallazgos

## Archivos principales

- `backend/app/governance_models.py`
- `backend/app/schemas_governance.py`
- `backend/app/services/governance_service.py`
- `backend/app/services/governance_masking.py`
- `backend/app/services/governance_adapters.py`
- `backend/app/routers/governance.py`
- `backend/alembic/versions/1350a1b2c3d4e_data_governance_1350.py`
- `frontend/src/pages/GobernanzaDatosPage.tsx`
- `tests/test_governance_1350.py`

## Resultados de verificación

| Área | Resultado |
|------|-----------|
| CATÁLOGO | PASS |
| CLASIFICACIÓN | PASS |
| LINAJE | PASS |
| USO POR IA | PASS |
| SALIDA PROVEEDORES | PASS |
| MINIMIZACIÓN | PASS |
| RETENCIÓN | PASS |
| DISPOSICIÓN | PASS |
| LEGAL HOLD | PASS |
| PROPÓSITO | PASS |
| AUTORIZACIONES | PASS |
| SOLICITUDES | PASS |
| EXPORTACIONES | PASS |
| ENMASCARAMIENTO | PASS |
| RIESGO | PASS |
| HALLAZGOS | PASS |
| RBAC | PASS |
| MULTIEMPRESA | PASS |
| AUDITORÍA | PASS |
| PREPARACIÓN 1270 | PASS |
| PREPARACIÓN 1330 | PASS |
| UI EN ESPAÑOL | PASS |
| ALEMBIC | PASS |
| ALEMBIC HEAD | `1350a1b2c3d4e` |
| TESTS | `713 passed, 1 failed, 2 skipped` (`test_governance_1350`: 28 passed) |
| FRONTEND | PASS (`npm run build`) |

## Defectos

| Nivel | Cantidad | Nota |
|-------|----------|------|
| P0 | 0 | — |
| P1 | 0 | — |
| P2 | 1 | `test_migration_roundtrip_upgrade_downgrade_upgrade` — fallo preexistente en base 1250a; no corregido según instrucción de bloque |

## Veredicto

**APTO** — Bloque 1350 funcional, auditable, aislado multiempresa, con migración propia y UI en español. Fallo de roundtrip Alembic histórico no atribuible a 1350.

## NO MERGE

Rama lista para revisión; no integrar sin proceso de convergencia acordado.
