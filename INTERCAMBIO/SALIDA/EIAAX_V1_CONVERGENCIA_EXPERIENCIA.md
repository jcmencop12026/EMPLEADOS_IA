# EIAAX V1 — Convergencia experiencia (macrobloque)

**Rama:** `cursor/experiencia-v1-convergencia-85e4`  
**Base autoritativa:** `104f7850d7196d08d80fff9b4e7a8a83a5a1fa9a`  
**Auditoría punto de partida:** `INTERCAMBIO/SALIDA/EIAAX_V1_AUDITORIA_TRANSVERSAL_POST_104f785.md`

---

## Capacidades reutilizadas

| Área | Origen | Uso |
|---|---|---|
| Demo comercial | `demo_comercial_service.py` | Semilla E2E Horizonte |
| Adjuntos evidencia | `evidencia_entrega_service` + espacio externo | Carga operador en cabina |
| Centro Control empresa | `CentroControlEmpresaPanel` | Contexto `?expediente=` |
| Cockpit CC | `CentroControlCockpit` + `CentroControlMasterAccess` | Consola maestra compacta |
| Guía 15 pasos | `guiaRapidaHelp.ts` | Parte 2 del instructivo |
| Tablas | Patrón `EiaaxTable` / popover columnas | KnowledgePage |

---

## Capacidades integradas / desarrolladas

### P0 — Logos
- `frontend/src/lib/logoUpload.ts` — resize cliente, entrada 2.5 MB, salida ~400 KB
- `EnterpriseLogoField.tsx` — optimización automática
- `AdminConfigPage.tsx` — marca madre con `BrandMark level="micro"`

### P0 — Documentos en cabina
- API `GET/POST /evaluaciones/{id}/informacion/{item_id}/adjuntos`
- `InformacionAdjuntosPanel.tsx` en Diagnóstico
- Botón «Sincronizar requisitos» en cabina

### P0 — Demo Clínica Demo Horizonte
- `demo_comercial_constants.py` — entidad «Clínica Demo Horizonte»
- `seed_demo_horizonte.py` — base `data/eiaax_horizonte_demo.db`
- Hallazgos, oportunidades, información adaptativa, indicadores ANTES/PROYECTADO/REAL

### P1 — UX transversal
- Menú `MENU_PRIMARY` + `MENU_ADVANCED` colapsable
- Layout `height: 100vh`, scroll lateral independiente
- CC compacto: ciclo, contexto empresa, sin duplicación vertical empresa/global
- KnowledgePage: botón «Columnas» compacto
- Instructivo 10 partes: `instructivoOperativo.ts` + `GuiaRapidaPage`

---

## Migraciones reconciliadas

Sin nuevas migraciones en este bloque. Head Alembic: `1820a1b2c3d4e`.

---

## Pruebas y resultados

| Suite | Resultado |
|---|---|
| `test_demo_comercial_ficticia.py` | 7/7 PASS |
| `test_convergencia_maestro_v1.py` | 6/6 PASS |
| `test_convergencia_cierre_v1.py` | 8/8 PASS |
| `test_presentacion_real_v1.py` | 9/9 PASS |
| `test_inteligencia_empresarial_evolution.py` | 9/9 PASS |
| `test_arquitecto_transformacion.py` | 8/8 PASS |
| `seed_demo_horizonte.py` | PASS |
| `git diff 0014a4b -- scripts/windows/` | 0 líneas (intacto) |

---

## Demo Horizonte — reproducción

```bash
python backend/scripts/seed_demo_horizonte.py
# Credenciales: admin / Admin2026!
# Centro de Control: /?expediente=<expediente_id>
```

Caso: reprocesos y demoras en facturación/radicación/auditoría documental.  
Etiqueta visible: **DEMO — DATOS SIMULADOS**.

---

## P0/P1/P2 restantes

| ID | Estado | Notas |
|---|---|---|
| P0 respaldo Windows | Separado | Documentado por Agente A — fuera de alcance |
| P1 Centro Operaciones densidad | Parcial | Requiere seed operativo adicional |
| P1 Presentación vs publicar UI | Parcial | Flujo existe; diferenciación visual pendiente |
| P2 Integración PR #162 económica | Pendiente | Cherry-pick `08e9ea1` + migración 1830 |
| P2 Integración PR #166 empresarial | **Parcial** | Módulo IE + API + escenarios ampliados; P0 import y P1 UI cadena pendientes |
| P2 Integración PR #163 empleado IA | Pendiente | Evaluar `bb6a379` selectivo |

---

## Riesgos

- Integración selectiva de PRs aislados no ejecutada en este entregable.
- Certificación visual Playwright requiere servicios en ejecución (no bloqueante para código).

---

## Instrucciones prueba humana (candidato)

1. Ejecutar `seed_demo_horizonte.py` o semilla `/api/demo-comercial/semilla`.
2. Login → Centro de Control → seleccionar «Clínica Demo Horizonte».
3. Recorrer: evaluación → Diagnóstico → cargar documento → hallazgos → oportunidades → presentación → Vista Empresa.
4. Configuración → Identidad → subir logo >180 KB (debe optimizarse).
5. Guía rápida e instructivo → 10 partes.
