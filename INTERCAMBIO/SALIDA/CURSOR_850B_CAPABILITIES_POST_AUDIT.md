# CURSOR-850B — Corrección post-auditoría Codex (PR #10)

**Rama:** `cursor/capabilities-tools-knowledge-testlab-850`
**PR:** #10 (draft, sin merge)
**HEAD ANTERIOR:** `218ed08`
**HEAD NUEVO:** _(post-commit)_

## Correcciones

| ID | Defecto Codex | Solución |
|----|---------------|----------|
| B1 | Tool ejecutada antes de approval | `evaluate_tool_execution` → REQUIRES_APPROVAL detiene ejecución; tool corre solo tras `approve` |
| B2 | `capability.requires_approval` ignorado | Incluido en política unificada |
| B3 | Permisos arbitrarios como autorización | `evaluate_tool_execution` no usa permisos API de usuario |
| B4 | Precedencia políticas | DENY > REQUIRES_APPROVAL > ALLOW en `authorization.py` |
| B5 | Test Lab bypass | Usa `run_controlled_plan` → misma política productiva |
| B7 | git diff --check FAIL | Trailing whitespace eliminado en doc de entrega |

## Arquitectura `authorization.py`

**Inputs:** tenant, employee, capability, tool, grant, `requires_approval` flags
**Output:** `ALLOW` | `DENY` | `REQUIRES_APPROVAL`
**Aplicación:** `coordinator._execute_task` antes de `_run_tool`

## Tests nuevos (`test_capabilities_850b.py`)

11 casos incluyendo contador de ejecución, approve/reject, precedencia y git diff check.

## Evidencia

```
TESTS PASSED: 73
FAILED: 0
NPM AUDIT: 0 HIGH/CRITICAL
BUILD: PASS
GIT diff --check: PASS
```

**RESULTADO: CURSOR-850B PASS**
