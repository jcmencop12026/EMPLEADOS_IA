# CURSOR — ORQUESTADOR-EXPERIENCIA-1010

**Rama:** `cursor/orquestador-experiencia-1010-12b6`  
**Base:** `main` @ `4a42c80`  
**Estado:** **LISTO PARA REAUDITORÍA**  
**Veredicto:** No merge a `main` ejecutado.

---

## 1. Arquitectura reutilizada

| Componente | Reutilización |
|------------|---------------|
| `AIEmployee`, `Capability`, `Tool` | Sin duplicar — selección sobre empleados existentes |
| `FinOpsRecord` | Señales de costo histórico por empleado |
| `salud_specialist_selection` | Delega a orquestador; conserva API y scoring base |
| `motor_analitico/pipeline` | Consume plan de especialistas enriquecido con roles |
| `IpsExperienceCase` | Se mantiene para SALUD; experiencia core es transversal |
| `salud_engine.run_ips_analysis` | Pasa `data_profiles` al orquestador |

**No se creó:** experiencia exclusiva SALUD, duplicado de AIEmployee/Knowledge/WorkPlan/MOTOR-1000.

---

## 2. Modelos nuevos

### `employee_experience_records` (transversal)

Campos: `organization_id`, `employee_id`, `dominio`, `tipo_problema`, `contexto_json`, `senales_json`, `hipotesis`, `decision`, `accion`, `resultado_esperado/real`, KPIs, valores, tiempos, `feedback_humano`, `estado` (EXITO/PARCIAL/FRACASO/INDETERMINADO), `peso_calidad`, condiciones éxito/fracaso, trazabilidad.

### `experience_selection_logs`

Trazabilidad: solicitud → candidatos → factores → experiencia consultada → seleccionados → roles → razón.

**Migración:** `1010a1b2c3d4e_orquestador_experiencia_1010.py` (head único).

---

## 3. Servicios

| Módulo | Responsabilidad |
|--------|-----------------|
| `experience_core.py` | CRUD experiencia, peso calidad explicable, similitud V1, feedback, actualización resultado |
| `orchestrator_selection.py` | Detección dominio principal, scoring 7 factores, roles equipo, diversidad |
| `salud_specialist_selection.py` | Fachada IPS → `select_team()` |

### API

- `POST /api/experiencia/registros`
- `PATCH /api/experiencia/registros/{id}/resultado`
- `POST /api/experiencia/registros/{id}/feedback`
- `GET /api/experiencia/similares`
- `POST /api/experiencia/seleccion-equipo`

---

## 4. Algoritmo de selección

### Factores y pesos

| Factor | Peso |
|--------|------|
| Capacidad | 25% |
| Experiencia | 20% |
| Desempeño | 15% |
| Costo (FINOPS) | 10% |
| Disponibilidad | 10% |
| Riesgo | 10% |
| Diversidad | 10% |

### Dominio principal

Detectado desde solicitud (no solo datos disponibles):

- Radicación tardía → `radicacion`
- Glosas/devoluciones → `glosas`
- Pagador lento (proceso sano) → `cartera`
- Diagnóstico integral → `estrategico`
- Datos insuficientes (cartera sin dataset) → `estrategico` + tipo `datos_insuficientes`

### Roles

| Rol | Cuándo |
|-----|--------|
| LÍDER | Mayor puntaje en dominio principal |
| ESPECIALISTA COMPLEMENTARIO | Otros dominios detectados |
| VALIDADOR | Impacto alto / múltiples dominios — especialidad diferente |
| DISIDENTE | Perspectiva alternativa (dominio contrastante) |

---

## 5. Diferencias A–E (MOTOR-1000)

| Caso | Dominio principal | Líder seleccionado |
|------|-------------------|-------------------|
| A | radicacion | Analista de Radicación IA |
| B | glosas | Analista de Glosas IA |
| C | cartera | Analista de Cartera IA |
| D | estrategico | Analista Estratégico IPS IA |
| E | estrategico (datos insuficientes) | Analista Estratégico IPS IA |

**Antes:** Analista de Cartera IA en los 5 casos.  
**Ahora:** 4 líderes distintos; E y D comparten estratégico con justificación diferente.

---

## 6. Demos

### Demo 1 — Especialista B gana por experiencia
Empleado glosas con 5 éxitos vs cartera con 5 fracasos → líder: Analista de Glosas IA.

### Demo 2 — Contexto determina líder
Caso A: solicitud enfatiza radicación → líder Radicación (sin experiencia seed extra).

### Demo 3 — Validador por diversidad
Caso D integral → validador con especialidad distinta al líder estratégico.

---

## 7. Multi-tenant

- Experiencia filtrada por `organization_id` en todas las consultas.
- Test `test_tenant_isolation_experiencia`: tenant B no ve experiencia de A.
- Sin experiencia global silenciosa.

---

## 8. FINOPS

- `FinOpsRecord.cost` alimenta factor costo (no criterio único).
- Caso glosas con cartera barata en FINOPS → sigue ganando especialista glosas por capacidad/experiencia.

---

## 9. Pruebas

**Archivo:** `tests/test_orquestador_experiencia_1010.py` — 23 tests:

1. experiencia exitosa  
2. fracaso  
3. sin seguimiento  
4. feedback bueno + resultado malo  
5. similitud alta  
6. similitud baja  
7. candidatos diferente experiencia  
8. costo diferente  
9. validador diversidad  
10. tenant isolation  
11. experiencia contradictoria  
12. experiencia antigua  
13. actualización resultado  
14. líder por tipo problema (parametrizado A–E)  
15. anti-líder-prefabricado  
16. fail-closed  
17. detect insuficiente  
18. demo B experiencia  
19. API selección equipo  

---

## 10. Regresión

| Control | Resultado |
|---------|-----------|
| pytest total | 459+ passed (1 flaky notifications preexistente) |
| motor_analitico_1000 | PASS |
| salud_960 | PASS |
| npm build | PASS |
| alembic heads | `1010a1b2c3d4e` |

---

## 11. UI

`DiagnosticoIpsPage.tsx` — sección Especialistas compacta:

- Líder + razón global
- Dominio principal
- Tabla roles (LÍDER, COMPLEMENTARIO, VALIDADOR, DISIDENTE)

---

## 12. Pendientes reales

- Embeddings para similitud (interfaz preparada, V1 estructurada).
- Sincronización bidireccional `IpsExperienceCase` ↔ `EmployeeExperienceRecord`.
- Dashboard de experiencia (fuera de alcance — no dashboard gigante).

---

## 13. Veredicto

**ORQUESTADOR-EXPERIENCIA-1010 — LISTO PARA REAUDITORÍA**

No merge a `main`.
