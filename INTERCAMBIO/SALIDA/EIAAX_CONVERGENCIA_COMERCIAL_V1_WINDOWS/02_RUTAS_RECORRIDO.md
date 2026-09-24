# Rutas para segundo recorrido humano

Acceso directo por URL tras login como `org_a_admin`.
No redisenadas — solo localizacion de rutas existentes.

Base: http://127.0.0.1:5180

---

## Nucleo operativo (ya en menu lateral)

| Area | Ruta | Menu / nota |
|------|------|-------------|
| Login | `/login` | Pantalla inicial |
| Inicio / Centro Control operacional | `/` o `/centro-control` | Inicio → Centro de Control |
| Empresas | `/administracion/empresas` | Administracion |
| Diagnostico | `/salud/diagnostico` | Salud → Diagnostico IPS |
| Centro Control MB-08 | `/centro-control` | Inicio |
| Evaluaciones / expediente | `/evaluaciones` | Analisis → Evaluaciones EIAAX |
| Oportunidades | `/oportunidades` | Analisis → Centro de oportunidades |
| Implementacion | `/implementacion` | Analisis |
| Empleados IA | `/directorio` | Empleados IA |
| Resultados | `/resultados` | Analisis → Inteligencia de resultados |
| Informes / comunicaciones | `/comunicaciones` | Analisis |
| Soporte | `/soporte` | Analisis → Mesa de Ayuda |
| Propuesta / comercial | `/comercial` | Analisis → Comercial y valor |
| Centro Negocios | `/centro-negocios` | Analisis |
| Arquitecto transformacion | `/arquitecto-transformacion` | Analisis |

---

## Rutas convergencia A+B+C+D (URL directa — no en sidebar)

| Area | Ruta | Bloque |
|------|------|--------|
| **Centro Estrategico** | `/centro-estrategico` | C |
| **Demo comercial** | `/demo` | D |
| Presentacion demo | `/demo/presentacion/{expedienteId}` | D |
| Presentacion real | `/presentacion/{expedienteId}` | D |
| Informes periodicos demo | `/demo/informes-periodicos` | D |
| **Portal espacio externo** | `/mi-espacio` | A (usuario `external_prospect`) |

---

## Flujo comercial sugerido (recorrido)

1. `/centro-estrategico` — cockpit 5 lecturas
2. `/evaluaciones` — expediente demo (codigo en seed JSON)
3. `/demo` — semilla demo comercial si aplica → presentacion
4. `/centro-negocios` o `/comercial` — propuesta
5. Admin: crear entidad espacio externo (API o futura UI admin)
6. Login prospecto → `/mi-espacio` — evidencias / vista entidad

---

## APIs de verificacion rapida (opcional)

| Check | URL |
|-------|-----|
| Health backend | http://127.0.0.1:8000/health |
| Health via proxy Vite | http://127.0.0.1:5180/health |
| Centro estrategico | http://127.0.0.1:8000/api/centro-estrategico/cockpit |
| Demo manifest | http://127.0.0.1:8000/api/demo-comercial/manifest |

Requieren token JWT tras login.

---

## Vista Entidad

- Interna: desde evaluacion / presentacion
- Externa: `/mi-espacio` → vista entidad (publicacion backend)
