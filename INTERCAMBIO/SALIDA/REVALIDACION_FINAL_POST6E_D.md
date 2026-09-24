# Revalidación visual final post-6E — Agente D

## SHA certificado

| Campo | Valor |
|---|---|
| HEAD corregido | `b0b27d5256933689917fbe711db2d3ccdb05b9a1` |
| Base anterior | `3a8b7e7ee18f81564c3a9f97d9fdf16b289f9b0b` |
| Rama | `cursor/correccion-focal-post6e-85e4` |
| Modo | Solo lectura / certificación visual focal |
| Fecha | 2026-08-30 |

Verificación previa:

```
git rev-parse HEAD → b0b27d5256933689917fbe711db2d3ccdb05b9a1
git show --no-patch --oneline HEAD → b0b27d5 docs: actualizar HEAD final entregable
```

## Contexto

Certificación anterior (post-6E sin corrección): P0=0, P1=3 (CC-01, CC-02, CC-03), P2=8.

Corrección General declarada: presentación/CSS/localización exclusivamente. Regresión declarada: 1235 passed, 0 failed.

## Entorno de revalidación

| Servicio | URL | Estado |
|---|---|---|
| Frontend | http://127.0.0.1:5180 | OK |
| Backend (proxy Vite) | http://127.0.0.1:8000 | OK (reinicio entorno para login) |
| Credenciales | admin / Admin2026* | Login OK |

**Nota entorno:** conflicto inicial puerto 8000 (login 500) resuelto reiniciando backend en HEAD certificado sin modificar código. No se alteró `vite.config.ts` ni lógica central.

---

## P1-CC-01 — Resumen ejecutivo

**Vista:** Centro de Control → Resumen → bloque "Resumen ejecutivo"

**Resultado: PASS**

| Criterio | Observación |
|---|---|
| Separación clara | KPI en tarjetas de grid independientes |
| Etiqueta legible | Labels visibles (ej. Organizaciones activas, Empleados IA activos) |
| Valor legible | Valores numéricos/texto debajo de cada etiqueta |
| Jerarquía visual | Etiqueta pequeña + valor destacado |
| Espaciado / alineación | Grid con gap uniforme, sin concatenación |
| Superposición / corte | No detectada |
| 1280 px | PASS |
| ~900 px (anchura inferior) | PASS — grid responsive, tarjetas distinguibles |

**Evidencia:** `/opt/cursor/artifacts/screenshots/revalidacion-d-cc-resumen-1280.png`, `revalidacion-d-cc-resumen-narrow.png`

---

## P1-CC-02 — Salud / Estado API

**Vista:** Centro de Control → Salud → "Salud de la plataforma"

**Resultado: PASS**

| Campo | Texto observado | ¿Crudo inglés? |
|---|---|---|
| Estado API | **Operativa** | NO — no aparece `up` |
| Base de datos | — | NO — no aparece `down`/`degraded`/`unknown` |
| Schedulers | — | NO — no aparece `down`/`degraded`/`unknown` |

**Evidencia:** `/opt/cursor/artifacts/screenshots/revalidacion-d-cc-salud-estado.png`

---

## P1-CC-03 — Auditoría reciente

**Vista:** Centro de Control → Salud → "Auditoría reciente"

**Resultado: PASS**

| Criterio | Observación |
|---|---|
| `auth.login` visible | **NO** |
| Etiqueta humana | **Inicio de sesión** (6 filas visibles) |
| Otros códigos crudos P1 | No detectados en filas visibles |

Filas observadas (muestra):

- Inicio de sesión | admin | 30/8/2026, 7:45:20 p. m.
- Inicio de sesión | admin | 30/8/2026, 7:44:53 p. m.
- Inicio de sesión | admin | 30/8/2026, 7:44:42 p. m.

**Evidencia:** `/opt/cursor/artifacts/screenshots/revalidacion-d-cc-auditoria.png`

---

## Regresión visual focal (mismas vistas)

**Resultado: PASS — sin P0/P1 visual nuevo detectado**

| Check | Estado |
|---|---|
| JSON crudo | No |
| UUID innecesario | No |
| Superposición | No |
| Botones desaparecidos | No |
| Navegación rota | No |
| Inglés residual P1 nuevo | No en vistas focalizadas |
| Degradación grave layout | No |

---

## P0 / P1 / P2

| Nivel | Antes corrección | Tras revalidación D |
|---|---|---|
| P0 | 0 | **0** |
| P1 | 3 (CC-01, CC-02, CC-03) | **0** (cerrados) |
| P2 | 8 | **8** (registrados, sin campaña) |

Ningún P2 elevado a P1/P0 por la corrección focal.

---

## Veredicto

**APTO PARA CONVERGENCIA FINAL**

Los tres P1 originales están cerrados visualmente en HEAD `b0b27d5`. No se detectó regresión visual P0/P1 inmediata en las vistas focalizadas.
