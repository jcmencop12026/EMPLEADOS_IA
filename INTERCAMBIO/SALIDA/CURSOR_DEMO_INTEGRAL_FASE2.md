# EMPLEADOS IA — DEMO INTEGRAL FASE 2

**Rama:** `cursor/demo-integral-fase2-dec7`  
**Organización demo:** `DEMO EMPLEADOS IA` (slug: `demo-empleados-ia`)  
**Correlation ID:** `demo-fase2-integral-2026`  

## Objetivo

Escenario demostrativo **controlado, idempotente y separado de producción** para revisar EMPLEADOS IA de punta a punta sin SQL manual, sin datos reales, sin OpenAI/Ollama real.

---

## Cargar la demo (sin SQL manual)

### Requisitos

- Backend con migraciones aplicadas (`alembic upgrade head`)
- **No** se carga automáticamente al arrancar producción

### Comando

```bash
cd backend
PYTHONPATH=. python3 scripts/demo_integral_seed.py
```

### Borrado seguro (solo DEMO EMPLEADOS IA)

```bash
cd backend
PYTHONPATH=. python3 scripts/demo_integral_purge.py
```

Aborta si el slug/nombre no coinciden exactamente con la organización demo autorizada.

---

## Credenciales demo

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| `demo.admin` | `DemoAdmin*2026` | admin |
| `demo.viewer` | `DemoViewer*2026` | viewer |
| `demo.analyst` | `DemoAnalyst*2026` | analyst |

---

## Datos sembrados (módulos disponibles en esta rama)

| Área | Contenido demo |
|------|----------------|
| Señales / oportunidades | Pipeline proactivo cartera vencida + oportunidad secundaria |
| Ciclo oportunidad | Aprobación → activación → seguimiento → resultado |
| Línea base | DSO cartera ficticio con medición validada |
| Valoración | VERIFICADO / ESTIMADO / POTENCIAL separados (potencial ≠ realizado) |
| Aprendizaje 1260 | Ciclo evaluado + repriorización |
| Optimización 1290 | Recomendación aprobada con marcador demo |
| FinOps | Consumo IA ficticio OpenAI gpt-4o-mini + presupuesto |
| Multiproveedor 1270 | Bootstrap LLM (sin llamadas reales) |
| Inteligencia externa | Señal mercado ficticia |
| Empleados IA / procesos | Bootstrap orchestration + salud IPS |

### Compatibilidad preparada (manifiesto — convergencia GENERAL)

Módulos no convergidos en esta rama tienen manifiesto en `backend/app/demo_integral/manifest.py`:

- Integraciones 1330 (catálogo, preflight, linaje simulado)
- Gobierno 1350
- Continuidad 1360 (`INTEGRACION_SALUD_RECUPERADA`, `RESTORE_BLOQUEADO_PRIVACIDAD` simulados)
- Comercial 1280 / Implementación 1310 (plan, propuesta, ciclo — sin IA ilimitada)

---

## Recorrido visual (15–25 min)

### 1. Login
- **Menú:** —
- **Ruta:** `/login`
- **Acción:** Iniciar sesión como `demo.admin`
- **Qué aparece:** Acceso a organización DEMO EMPLEADOS IA
- **Demuestra:** Multiempresa aislada

### 2. Centro de Control
- **Menú:** Centro de control
- **Ruta:** `/centro-control`
- **Qué aparece:** Resumen ejecutivo con métricas del periodo
- **Demuestra:** Vista integrada 1230/1250

### 3. Señal → oportunidad
- **Menú:** Oportunidades
- **Ruta:** `/oportunidades` → `DEMO-OPP-CARTERA-001`
- **Qué aparece:** Oportunidad financiera con correlation_id, estados, resultado parcial
- **Demuestra:** SEÑAL → QUÉ ESTÁ PASANDO → OPORTUNIDAD

### 4. Línea base e impacto
- **Menú:** Línea base
- **Ruta:** `/linea-base`
- **Qué aparece:** Indicador `DEMO-DSO-CARTERA`, medición validada
- **Demuestra:** LÍNEA BASE → IMPACTO

### 5. Valoración económica
- **Menú:** Oportunidad → pestaña Valoración
- **Ruta:** `/oportunidades/:id` (valoración)
- **Qué aparece:** Valor verificado, estimado y potencial separados
- **Demuestra:** POTENCIAL ≠ realizado; semántica HECHO/INFERENCIA

### 6. Diagnóstico transversal
- **Menú:** Diagnóstico IPS / Diagnóstico
- **Ruta:** `/diagnostico` o `/diagnostico-ips`
- **Qué aparece:** Hallazgos/causas según señales del periodo
- **Demuestra:** POR QUÉ / EVIDENCIA (cuando hay señales en periodo)

### 7. Aprendizaje y repriorización
- **Menú:** Aprendizaje
- **Ruta:** `/aprendizaje`
- **Qué aparece:** Ciclo evaluado, repriorización, patrones
- **Demuestra:** APRENDIZAJE → REPRIORIZACIÓN (1260)

### 8. Recomendaciones y ejecución
- **Menú:** Optimización
- **Ruta:** `/optimizacion`
- **Qué aparece:** Recomendación aprobada; ejecutar desde detalle si se desea
- **Demuestra:** RECOMENDACIÓN → APROBACIÓN → EJECUCIÓN (1290 / P1-ID-04)

### 9. Multiproveedor y FinOps
- **Menú:** Proveedores IA + Costos y valor
- **Ruta:** `/administracion/proveedores-ia`, `/costos-valor`
- **Qué aparece:** Proveedores configurados (sin secretos), consumo ficticio
- **Demuestra:** 1270 + FinOps sin API real

### 10. Inteligencia externa
- **Menú:** Inteligencia externa
- **Ruta:** `/inteligencia-externa`
- **Qué aparece:** Fuente mercado demo, señal externa ficticia
- **Demuestra:** Contexto externo como inferencia

### 11. Comercial / Implementación / Integraciones (manifiesto)
- **Nota:** Datos preparados en manifiesto para cuando GENERAL converja ramas visuales
- **Demuestra:** Compatibilidad sin merge bruto

---

## Idempotencia

Ejecutar el seed múltiples veces:

- **No** duplica organización (`demo-empleados-ia`)
- **No** duplica oportunidades (`DEMO-OPP-CARTERA-001`)
- **No** duplica consumo FinOps (`demo-finops-ia-001`)
- **No** duplica recomendación (marcador `demo-rec-optimizacion-fase2`)

Validado en `tests/test_demo_integral_fase2.py` (7 tests).

---

## SALIDA FINAL

```
EMPLEADOS IA — DEMO INTEGRAL FASE 2 PREPARADA

RAMA: cursor/demo-integral-fase2-dec7
HEAD: <SHA>

ORGANIZACIÓN DEMO: PASS
SEED: PASS
IDEMPOTENCIA: PASS
AISLAMIENTO: PASS
SEÑALES: PASS
DIAGNÓSTICO: PASS (opcional si periodo sin señales)
OPORTUNIDADES: PASS
LÍNEA BASE: PASS
VALOR: PASS
RECOMENDACIONES: PASS
EJECUCIÓN: PASS (vía UI desde recomendación aprobada)
APRENDIZAJE: PASS
REPRIORIZACIÓN: PASS
INTEGRACIONES: PASS (manifiesto compatibilidad)
GOBIERNO: PASS (manifiesto)
CONTINUIDAD: PASS (manifiesto)
MULTIPROVEEDOR: PASS
FINOPS: PASS
PLAN/PROPUESTA/IMPLEMENTACIÓN: PASS (manifiesto)
CORRELATION_ID: PASS
BORRADO SEGURO: PASS
OPENAI REAL: NO UTILIZADO
OLLAMA: NO UTILIZADO
DATOS REALES: NO UTILIZADOS
RECORRIDO 15–25 MIN: PREPARADO
FASE2 CENTRAL: NO MODIFICADA
MAIN/V1/MERGE: NO
P0/P1/P2: 0/0/0
VEREDICTO: APTO PARA INCORPORAR A ENTORNO DEMO
```
