# CURSOR V1 - Certificacion OpenAI real e8cb853

## Rama de herramientas

| Campo | Valor |
|-------|-------|
| Rama | `cursor/v1-certificacion-openai-tools` |
| Base tools | `cursor/v1-certificacion-windows-tools` @ `c7cb55cd4ad906b064d2105c4e75be9fbe466e73` |
| Candidata | `e8cb853a2c447fd5e136a0907e44d68ce2c8cf81` |
| Script | `scripts/CERTIFICAR_V1_OPENAI_REAL_E8CB853.ps1` |

Esta rama contiene **unicamente** herramientas de certificacion OpenAI real.  
**No** modifica la candidata V1, `main` ni PR #32.

---

## Gates cerrados localmente

| Gate | Descripcion |
|------|-------------|
| GATE-02 | OpenAI real via gateway plataforma |
| UAT-015 | Inferencia OpenAI real (provider, modelo, tokens, anti-mock) |
| UAT-020 | Trazabilidad FinOps + inference log + auditoria |

---

## Pre-requisitos

1. Certificacion Docker Windows completada (stack `empleados_ia_cert` operativo).
2. `D:\EMPLEADOS_IA_CERT` en SHA `e8cb853` sin cambios versionados.
3. `OPENAI_API_KEY` definida en el entorno Windows del operador.
4. El contenedor **backend** debe recibir `OPENAI_API_KEY` (anadir a `.env` local de certificacion y reiniciar backend).

Evidencias previas en `INTERCAMBIO/SALIDA/CERT_WINDOWS_E8CB853_EVIDENCIA/` son **permitidas** y no abortan el script.

---

## Ejecucion

```powershell
Set-Location D:\EMPLEADOS_IA_CERT_TOOLS
Set-ExecutionPolicy -Scope Process Bypass -Force
.\scripts\CERTIFICAR_V1_OPENAI_REAL_E8CB853.ps1
```

### Sin credencial local

```
OPENAI REAL: PENDIENTE POR CREDENCIAL LOCAL AUSENTE
```

- 0 llamadas pagadas
- No se muestra longitud, prefijo ni fragmento de la clave

---

## Flujo tecnico (una sola llamada)

1. Prevalidacion candidata (git root, SHA, cambios versionados)
2. Verificacion `OPENAI_API_KEY`: PRESENTE / AUSENTE
3. Login plataforma via `http://127.0.0.1:15180/api/auth/login`
4. **Una** llamada: `POST /api/llm/complete` con prompt `Responde solamente: OK`
5. Validacion gateway: provider `openai`, modelo real, tokens, trace_id
6. Verificacion `GET /api/llm/inference-logs`
7. Verificacion `GET /api/finops/consumptions?provider=openai`
8. Verificacion `GET /api/audit/logs` (accion `llm.inference.success`)

Ruta completa:

```
API plataforma -> gateway IA -> adaptador OpenAI -> OpenAI real
```

Sin bypass del gateway.

---

## Evidencia

Directorio:

`D:\EMPLEADOS_IA_CERT\INTERCAMBIO\SALIDA\CERT_OPENAI_REAL_E8CB853_EVIDENCIA\`

Archivos:

- `certificacion_openai.log` (sin secretos)
- `evidencia_openai.json`
- `RESUMEN.txt`

Informe generado:

`INTERCAMBIO/SALIDA/CURSOR_V1_CERTIFICACION_OPENAI_REAL_E8CB853.md`

---

## Anti-mock

El script valida:

- `provider == openai`
- modelo no contiene `mock|fixture|fake`
- `tokens_total > 0`
- `trace_id` presente en inference log
- registro FinOps asociado a la organizacion
- auditoria `llm.inference.success`

No imprime API key, Authorization ni headers sensibles.

---

## Pruebas sin costo

```powershell
.\scripts\TEST_CERTIFICAR_OPENAI_REAL_FLOW.ps1
```

Valida deteccion AUSENTE/PRESENTE, rutas de evidencia, redaccion de secretos y que solo exista una llamada `/api/llm/complete` en el script.

Modo prueba del script principal (bloquea llamada real):

```powershell
.\scripts\CERTIFICAR_V1_OPENAI_REAL_E8CB853.ps1 -TestMode
```

---

## NO hacer desde Cloud Agent

No ejecutar el script de certificacion real desde Cloud Agent (sin `OPENAI_API_KEY` local del operador).

**NO MERGE**
