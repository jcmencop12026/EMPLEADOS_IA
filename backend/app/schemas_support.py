"""Esquemas Pydantic — Mesa de Ayuda y Soporte (MB-12)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SupportCaseCreate(BaseModel):
    tipo: str = Field(default="SOLICITUD", max_length=40)
    categoria: str | None = Field(default=None, max_length=80)
    asunto: str = Field(min_length=3, max_length=300)
    descripcion: str = Field(min_length=3)
    prioridad: str | None = Field(default=None, max_length=20)
    impacto: str = Field(default="MEDIO", max_length=20)
    urgencia: str = Field(default="MEDIA", max_length=20)
    modulo_relacionado: str | None = None
    entidad_relacionada: str | None = None
    servicio_componente: str | None = None
    correlation_id: str | None = None
    evidencia_ref: str | None = Field(default=None, max_length=500)
    grupo: str | None = None
    es_incidente_mayor: bool = False


class SupportCaseAutoCreate(BaseModel):
    tipo: str
    asunto: str
    descripcion: str
    prioridad: str | None = None
    impacto: str = "MEDIO"
    urgencia: str = "MEDIA"
    origen_tipo: str
    origen_id: str
    modulo_relacionado: str | None = None
    entidad_relacionada: str | None = None
    servicio_componente: str | None = None
    correlation_id: str | None = None
    solicitante_id: str | None = None


class SupportCaseAssign(BaseModel):
    responsable_id: str | None = None
    grupo: str | None = None
    responsable_tecnico_id: str | None = None
    responsable_funcional_id: str | None = None


class SupportAssigneeOut(BaseModel):
    id: str
    nombre: str
    username: str
    email: str | None = None
    rol: str
    etiqueta: str


class SupportCaseStatusUpdate(BaseModel):
    estado: str
    nota: str | None = None


class SupportCaseResolve(BaseModel):
    resolucion: str = Field(min_length=3)
    cerrar: bool = False


class SupportCaseClose(BaseModel):
    nota: str | None = None


class SupportCommentCreate(BaseModel):
    cuerpo: str = Field(min_length=1)
    es_interno: bool = False
    evidencia_ref: str | None = Field(default=None, max_length=500)


class SupportSlaPolicyCreate(BaseModel):
    nombre: str
    prioridad: str = "MEDIA"
    tipo_caso: str | None = None
    servicio: str | None = None
    minutos_primera_respuesta: int | None = None
    minutos_resolucion: int | None = None
    horario_servicio_json: dict[str, Any] | None = None


class SupportPrioritySuggest(BaseModel):
    impacto: str
    urgencia: str


class SupportPriorityUpdate(BaseModel):
    prioridad: str
    motivo: str | None = None


class SupportClassify(BaseModel):
    tipo: str | None = None
    categoria: str | None = None
    servicio_componente: str | None = None


class SupportEscalate(BaseModel):
    motivo: str
    nota: str | None = None
    coordinador_id: str | None = None


class SupportDiagnosisUpdate(BaseModel):
    sintoma: str | None = None
    hipotesis: str | None = None
    causa_probable: str | None = None
    causa_validada: str | None = None


class SupportEvidenceCreate(BaseModel):
    tipo: str
    referencia: str = Field(max_length=500)
    descripcion: str | None = None


class SupportValidateResolution(BaseModel):
    aceptada: bool
    comentario: str | None = None


class SupportProblemCreate(BaseModel):
    titulo: str = Field(min_length=3, max_length=300)
    descripcion: str = Field(min_length=3)
    case_ids: list[str] = Field(min_length=1)


class SupportProblemUpdate(BaseModel):
    causa_raiz: str | None = None
    solucion_temporal: str | None = None
    solucion_definitiva: str | None = None
    acciones_preventivas: str | None = None
    estado: str | None = None


class SupportKnowledgeProposalCreate(BaseModel):
    titulo: str = Field(min_length=3, max_length=300)
    contenido: str = Field(min_length=3)
    tipo_articulo: str = "PROCEDIMIENTO"
    case_id: str | None = None
    problem_id: str | None = None


class SupportPostReviewUpsert(BaseModel):
    que_ocurrio: str | None = None
    impacto: str | None = None
    causa: str | None = None
    que_se_hizo: str | None = None
    tiempos: str | None = None
    que_funciono: str | None = None
    que_fallo: str | None = None
    accion_preventiva: str | None = None
    responsable_id: str | None = None
    fecha_objetivo: datetime | None = None


class SupportAutoservicioQuery(BaseModel):
    consulta: str = Field(min_length=2)


class SupportCaseOut(BaseModel):
    id: str
    organization_id: str
    numero: int
    referencia: str
    tipo: str
    categoria: str | None = None
    asunto: str
    descripcion: str | None = None
    prioridad: str
    prioridad_sugerida: str | None = None
    impacto: str
    urgencia: str
    estado: str
    solicitante_id: str
    responsable_id: str | None = None
    responsable_tecnico_id: str | None = None
    responsable_funcional_id: str | None = None
    coordinador_id: str | None = None
    grupo: str | None = None
    modulo_relacionado: str | None = None
    entidad_relacionada: str | None = None
    servicio_componente: str | None = None
    problema_id: str | None = None
    es_incidente_mayor: bool = False
    correlation_id: str | None = None
    origen: str
    origen_tipo: str | None = None
    origen_id: str | None = None
    resolucion: str | None = None
    sintoma: str | None = None
    hipotesis: str | None = None
    causa_probable: str | None = None
    causa_validada: str | None = None
    validacion_solicitante: str | None = None
    validacion_at: datetime | None = None
    escalamiento_nivel: int = 0
    sla_estado: str | None = None
    primera_respuesta_limite: datetime | None = None
    resolucion_limite: datetime | None = None
    fecha_limite: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    resuelto_at: datetime | None = None
    cerrado_at: datetime | None = None
    clasificado_at: datetime | None = None


class SupportHistoryOut(BaseModel):
    id: str
    accion: str
    usuario_id: str | None = None
    detalle: dict[str, Any] | None = None
    correlation_id: str | None = None
    created_at: datetime | None = None


class SupportCommentOut(BaseModel):
    id: str
    usuario_id: str
    cuerpo: str
    es_interno: bool
    evidencia_ref: str | None = None
    created_at: datetime | None = None


class SupportEvidenceOut(BaseModel):
    id: str
    tipo: str
    referencia: str
    descripcion: str | None = None
    usuario_id: str | None = None
    created_at: datetime | None = None


class SupportCaseDetailOut(SupportCaseOut):
    responsable_nombre: str | None = None
    responsable_email: str | None = None
    historial: list[SupportHistoryOut] = Field(default_factory=list)
    comentarios: list[SupportCommentOut] = Field(default_factory=list)
    evidencias: list[SupportEvidenceOut] = Field(default_factory=list)
    problema: dict[str, Any] | None = None
    revision_posterior: dict[str, Any] | None = None


class SupportContratoMiTrabajo(BaseModel):
    casos_asignados: int
    casos_vencidos: int
    casos_accion_requerida: int
    endpoint: str = "/api/soporte/contrato/mi-trabajo"


class SupportContratoCentroControl(BaseModel):
    casos_abiertos: int
    casos_criticos: int
    casos_vencidos: int
    tiempo_medio_respuesta_min: float | None = None
    tiempo_medio_resolucion_min: float | None = None
    principales_categorias: list[dict[str, Any]] = Field(default_factory=list)
    endpoint: str = "/api/soporte/contrato/centro-control"
