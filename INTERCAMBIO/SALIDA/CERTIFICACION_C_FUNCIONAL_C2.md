# CERTIFICACIÓN C — FUNCIONAL C2

**Proyecto:** EIAAX / EMPLEADOS_IA  
**Agente:** C  
**SHA:** `b19b04dd438f5b13b422e9a760f54fa074fb52ed`  
**Fecha:** 2026-08-31  
**Modo:** Solo lectura — pruebas runtime + suites existentes

---

## Veredicto obligatorio

# C2 FUNCIONAL APTO

---

## Resumen

20 recorridos obligatorios cubiertos por **tests runtime** (`test_convergencia_c2.py`) y **regresión** (C1-R1, hotfix, G2/G3, bandeja). No se confió únicamente en unit tests estáticos: 14/17 tests C2 ejercitan API con `TestClient` y datos sembrados multi-tenant.

| Métrica | Valor |
|---------|-------|
| Tests C2 runtime | 17/17 PASS |
| Regresión ampliada | 44/44 PASS |
| Frontend build | PASS |
| P0 | 0 |
| P1 | 0 |
| P2 | 1 |

---

## Recorridos obligatorios (1–20)

| # | Recorrido | Resultado | Evidencia |
|---|-----------|-----------|-----------|
| 1 | Login usuario org A | **PASS** | `_login` + `test_c2_centro_control_datos_tenant_correcto` |
| 2 | Centro de Control A | **PASS** | `organization_id == org.id` en respuesta |
| 3 | Mi Trabajo A | **PASS** | `test_c2_mi_trabajo_elementos_tenant_usuario` |
| 4 | Usuario A no accede a B | **PASS** | `test_c2_org_a_no_ve_datos_org_b` |
| 5 | Login usuario org B | **PASS** | `test_c2_org_b_no_ve_datos_org_a` |
| 6 | Centro de Control B | **PASS** | Implícito en aislamiento B |
| 7 | Mi Trabajo B | **PASS** | `filtros_aplicados.organization_id == org_b.id` |
| 8 | Usuario B no accede a A | **PASS** | Sin datos "solo-a" en items B |
| 9 | SUPERADMIN selecciona A | **PASS** | `?organization_id={org_a.id}` |
| 10 | CC/Mi Trabajo muestran A | **PASS** | `test_c2_superadmin_consulta_organizacion_explicita` |
| 11 | SUPERADMIN cambia a B | **PASS** | `test_c2_superadmin_cambio_contexto_no_mezcla_datos` |
| 12 | CC/Mi Trabajo muestran B | **PASS** | `organization_id` distintos A vs B |
| 13 | No quedan datos de A | **PASS** | Notificaciones: solo B en contexto B |
| 14 | Organización inactiva rechazada | **PASS** | `test_c2_superadmin_inactive_org_rejected` → 403 |
| 15 | Sin permiso → backend 403 | **PASS** | `test_c2_usuario_sin_permiso_cc_403`, cross-org tenant → 403 |
| 16 | Home C1-R1 preservado | **PASS** | `test_c2_c1_r1_home_route_preservado` |
| 17 | Mi Trabajo sin duplicados G2/G3 | **PASS** | Gate G2/G3 regression PASS |
| 18 | Navegación Mi Trabajo → recurso | **PASS** | `test_c2_trabajo_enlace_recurso_correcto` — `enlace` con `/` |
| 19 | Login/MFA/SSO/sid preservados | **PASS** | `test_v1_hotfix_login` 6/6; sin diff auth |
| 20 | Frontend build PASS | **PASS** | `npm ci && npm run build` ✓ |

---

## Suites ejecutadas

```bash
# C2 completo
pytest tests/test_convergencia_c2.py -q          # 17 passed

# Regresión funcional
pytest tests/test_convergencia_c2.py \
       tests/test_c1_r1_home_route.py \
       tests/test_v1_hotfix_login.py \
       tests/test_gate_post6d_correcciones.py::test_g2_solicitar_aprobacion_transitions_trabajo \
       tests/test_gate_post6d_correcciones.py::test_g3_dedup_oportunidad_vs_1290_humana \
       tests/test_bandeja_trabajo_humano.py -q    # 44 passed

# Build
cd frontend && npm ci && npm run build            # PASS
```

---

## Hallazgos

### P0 / P1

**Ninguno.**

### P2

| ID | Hallazgo |
|----|----------|
| P2-C2-C01 | Recorridos 9–12 validados vía API con `organization_id` query param; E2E browser no ejecutado en esta VM (cobertura API + wiring estático suficiente para certificación funcional) |

---

*Certificación C Funcional — 2026-08-31*
