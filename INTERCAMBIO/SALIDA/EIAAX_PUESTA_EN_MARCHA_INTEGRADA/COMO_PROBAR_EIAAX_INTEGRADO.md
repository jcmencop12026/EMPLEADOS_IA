# Cómo probar EIAAX integrado (Lote 3)

## 1. Requisitos

- Python 3.12+, Node 20+
- Repositorio en rama `cursor/integracion-lote-3-85e4` (SHA `233075a` o tag respaldo `e0f4b07`)

## 2. Base de datos y semilla

```bash
cd backend
export DATABASE_URL=sqlite:////workspace/data/eiaax_integrado_demo.db
alembic upgrade head
python3 scripts/seed_lote3_demo.py
```

Credenciales demo: ver `backend/scripts/credentials.example` (no publicar en producción).

| Usuario | Rol | Organización |
|---------|-----|--------------|
| org_a_admin | admin | Empresa Demo A |
| org_a_viewer | viewer | Empresa Demo A |
| org_b_admin | admin | Empresa Demo B |

## 3. Backend

```bash
cd backend
export DATABASE_URL=sqlite:////workspace/data/eiaax_integrado_demo.db
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Verificar: `GET http://localhost:8000/health` → `status: up`

## 4. Frontend

```bash
cd frontend
npm install   # solo primera vez
npm run dev -- --host 0.0.0.0 --port 5180
```

Abrir: **http://localhost:5180**

Login: `org_a_admin` / contraseña en `credentials.example`

## 5. Recorrido recomendado

1. **Inicio** — Centro de Control
2. **Evaluaciones** — expediente EVA-2026-0001
3. **Centro de Negocios** — pipeline y propuesta demo
4. **Arquitecto de Transformación** — dossier y necesidad
5. **Resultados** — indicadores ANTES/PROYECTADO/REAL
6. **Soporte** — caso demo
7. **Centro de Confianza** — gobierno
8. **Multiempresa** — login `org_b_admin`, confirmar que no ve datos de Org A

## 6. Pruebas automatizadas

```bash
# Regresión Lote 2 + Lote 3
python3 -m pytest tests/test_bloque_producto_1_evaluacion.py ... tests/test_multitenant_v1.py -q

# Recorridos demo (requiere BD semilla)
DATABASE_URL=sqlite:////workspace/data/eiaax_integrado_demo.db \
  python3 -m pytest tests/test_puesta_en_marcha_journeys.py -v
```

## 7. Build frontend

```bash
cd frontend && npm run build
```

## 8. Detener servicios

`Ctrl+C` en terminales de uvicorn y vite.

## 9. Qué esperar

- Sidebar en español con módulos Lote 3 (Centro Negocios, Arquitecto, Resultados)
- RBAC: viewer no ve economía privada
- Gobierno Operacional como autoridad de aprobaciones
- EIAAX funcional sin PIIAX (estados controlados si capacidad externa ausente)
