# 03 — Autoridades canónicas recomendadas

**Regla:** una autoridad por dominio. Los candidatos aportan **implementación** o **adapters**; no autoridades paralelas permanentes.

---

## Tabla de unificación (9 autoridades)

| # | Dominio | Duplicidad detectada | Autoridad final recomendada | Acción sobre candidatos |
|---|---------|----------------------|----------------------------|-------------------------|
| 1 | **Dossier** | B orquesta, C dossier transformación, D demo seed | `EvaluacionExpediente` + `transformacion` (C) como vista enriquecida | **R** central · **K** C dossier · **X** dossier paralelo |
| 2 | **Prospecto/cliente externo** | A `EntidadEmpresa`, B estados flujo | `EntidadEmpresa` + `estado_relacion` (A) como identidad externa; B orquesta transición | **P** A · **K** B `promote_to_cliente`→A |
| 3 | **Publicación** | A `EmpresaPublicacion`, D `PresentacionPublicacion`, C `evaluacion.visibility` | **UNA:** capa `PublicacionEmpresa` conceptual = A estados + audiencia + paquetes; D y C como **consumidores/adapters** | **P** A núcleo · **K** D fail-closed · **K** C selección · **X** tercera tabla publicación |
| 4 | **Visibilidad gobierno (4 niveles)** | A 1420, central modelos | `empresa_seguridad` + `gobierno_operacional.visibility` (A) | **P** A · no duplicar en C/D |
| 5 | **Evidencias** | A adjuntos, central `evidencia_ref`, `EmpresaEvidenciaVinculo` | `EvaluacionEntregaAdjunto` + `knowledge_storage/EVIDENCE_ROOT` + `EmpresaEvidenciaVinculo` | **P** A · **R** vínculo 1420 |
| 6 | **Economía** | B `economic_motor_*`, C `strategic_economy`, central FinOps | `economic_motor_service` (1600) como **única** capa; C solo lectura privada | **P** B motor · **K** C adapter · **X** motor estratégico duplicado |
| 7 | **Resultados** | D `resultados_models` ext., A adaptador vista | `resultados_service` + semántica ANTES/PROYECTADO/REAL | **P** D métricas · **K** A filtro externo |
| 8 | **Informes** | A portal adapter, D `informes_comerciales_adapter` | **MB-11** `communications_service` + `CommMessage` | **R** MB-11 · **K** A/D adapters |
| 9 | **Presentación ejecutiva** | B `ComercialPresentacionEjecutiva`, D PDF+publicación, C cockpit | Orquestación B selección contenido + render D PDF + publicación A paquete `PROPUESTA/RESULTADOS` | **K** los tres · **?** modelo único selección |

---

## Detalle por dominio

### Dossier
- **Canónico:** `evaluaciones_expediente` + ítems información + hallazgos.
- **C** aporta capa diagnóstico/mapa sin reemplazar expediente.
- **D** usa prefijos demo — no mezclar con producción sin flag.

### Organización / empresa
- **Canónico:** `organizations` (tenant).
- **A:** `EntidadEmpresa` = proyección comercial externa 1:1 expediente (no segunda org).
- **C:** Partners = grant cross-org (MB-03), distinto de EntidadEmpresa.

### Publicación (decisión crítica)

| Fuente | Mecanismo | Estados |
|--------|-----------|---------|
| A | `EmpresaPublicacion` por paquete | PRIVADO → PREPARADO_PRESENTAR → PUBLICADO_EMPRESA |
| D | `PresentacionPublicacion` | PRIVADO → PUBLICADO (fail-closed) |
| C | metadata en payload | delega `evaluacion.visibility` |
| Central | `evaluacion.visibility` + hallazgo `visible_entidad` | — |

**Recomendación GENERAL:**

1. **Autoridad de transición:** A `EmpresaPublicacion` (versionado, audiencia GERENCIA/OPERACIÓN/SISTEMAS/FINANCIERO).
2. **Autoridad de contenido:** `evaluacion.visibility` (qué objetos existen).
3. **D `PresentacionPublicacion`:** convertir en **adapter** que consulta A+visibility; **DESCARTAR** tabla independiente a largo plazo.
4. **C publicación:** solo UI/selección; no persistir segundo estado.

### Economía
- **Canónico:** `economic_motor_service` + FinOps.
- **B:** extiende 1600-1730 — fuente de verdad precio/costo.
- **C `strategic_economy_service`:** solo lectura agregada para cockpit; **nunca** escribe precio.
- **Regla:** economía privada RBAC `*.economy.private` / `strategic_control.economia_privada`; POTENCIAL ≠ REAL (B y C alineados).

### Informes
- **Canónico:** MB-11 (`comm_messages`, reglas, canales).
- **D `InformeComercialConfig`:** configuración comercial → dispara MB-11, **sin scheduler propio**.
- **A:** filtra `CommMessage` ENVIADA/ENTREGADA para portal externo.

### Implementación / Empleados IA / Soporte
- **Canónico:** servicios existentes (`implementacion_service`, `agent_factory`, `support_service`).
- **A:** únicos adapters externos autorizados — **no** segundos módulos.

### Auditoría / correlation_id
- **Canónico:** `write_audit` transversal.
- Normalizar: `correlation_id` expediente = entidad = entregas = adjuntos; demo prefix aislado.

---

## Audiencias (4) — convergencia

| Rama | Implementación |
|------|----------------|
| A | `AUDIENCIAS_PUBLICACION` en `EmpresaPublicacion.audiencia` |
| C | `LECTURAS` = GERENCIA, OPERACIÓN, SISTEMAS, FINANCIERO (mismo dossier) |
| D | `AUDIENCIAS` en demo constants + informes config |

**Recomendación:** enum único `GERENCIA|OPERACION|SISTEMAS|FINANCIERO` en capa publicación (A); C/D consumen sin replicar datos.
