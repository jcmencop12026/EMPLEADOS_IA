# QA-INFRA-001 — Certificación automática

Documentación breve para el equipo sobre la infraestructura de CI de EMPLEADOS_IA.

## Qué ejecuta CI

El workflow `.github/workflows/qa.yml` (**Certificación QA**) valida automáticamente:

| Job | Qué hace |
|-----|----------|
| **Backend y PostgreSQL** | Instala Python, conecta a PostgreSQL efímero, ejecuta migraciones Alembic y `pytest` |
| **Frontend** | `npm ci`, `npm run build`, `npm audit` |
| **Validación Git** | `git diff --check` contra `main` |
| **Pruebas Windows** | Tests de arranque SQLite en `windows-latest` |

## Cuándo se ejecuta

- En cada **Pull Request**
- **Manualmente** desde GitHub → Actions → *Certificación QA* → *Run workflow*

### Parámetro manual opcional

`grupo_focal`: permite ejecutar un subconjunto de tests:

- Marcador: `auth`, `tenant`, `operations`, `migrations`, etc.
- Ruta: `tests/test_orchestrator_e2e.py`

## Python

Versión definida en `.python-version` (3.12), alineada con el entorno local `py -3`.

## PostgreSQL en CI

- Contenedor efímero `postgres:16`
- Credenciales de prueba únicamente (`empleados_test` / `empleados_ia_test`)
- Sin secretos reales ni BD externa permanente
- Migraciones: `upgrade head` → `downgrade` a revisión base → `upgrade head`

## Cómo agregar tests focales

1. Marcar el test en `pytest.ini` (marcadores registrados).
2. Añadir decorador o `pytestmark` en el archivo de test:

```python
import pytest

pytestmark = pytest.mark.operations
```

3. En CI manual, usar `grupo_focal: operations`.

Marcadores disponibles: `auth`, `tenant`, `knowledge`, `notifications`, `automations`, `migrations`, `operations`, `windows`.

## Reglas

- Los jobs obligatorios **no** usan `continue-on-error`.
- Si un control falla, el workflow falla (PASS/FAIL real).
- No se despliega nada automáticamente.

## Ejecución local recomendada

```bash
python -m pytest
cd frontend && npm run build && npm audit
git diff --check origin/main...HEAD
```

Para simular PostgreSQL localmente:

```bash
export DATABASE_URL=postgresql+psycopg2://empleados_test:empleados_test@localhost:5432/empleados_ia_test
cd backend && PYTHONPATH=. alembic upgrade head
cd .. && python -m pytest
```

## Limitaciones

- GitHub Actions remoto no se ejecuta desde este entorno de agente; validar en GitHub tras abrir PR.
- Tests de automatizaciones/scheduler (`automations`) se ejecutarán cuando se integren en `main`; la infraestructura ya admite el marcador.
