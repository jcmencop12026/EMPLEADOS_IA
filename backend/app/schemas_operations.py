from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class OperationSummaryOut(BaseModel):
    running: int = 0
    pending: int = 0
    approval: int = 0
    error: int = 0
    overdue: int = 0
    due_soon: int = 0


class OperationItemOut(BaseModel):
    id: str
    trabajo: str
    proceso: str | None = None
    responsable: str | None = None
    empleado_ia: str | None = None
    prioridad: str = "Media"
    prioridad_codigo: str = "MEDIA"
    estado: str
    estado_codigo: str
    progreso: str
    aprobaciones_pendientes: int = 0
    inicio: datetime | None = None
    vencimiento: datetime | None = None
    vencimiento_estado: str = "Sin vencimiento"
    vencimiento_codigo: str = "sin_vencimiento"
    ultima_actividad: datetime | None = None
    resultado: str | None = None
    approval_status: str
    confidence: float | None = None
    correlation_id: str
    employee_id: str | None = None
    acciones: list[str] = Field(default_factory=list)


class OperationTaskOut(BaseModel):
    id: str
    titulo: str
    responsable: str | None = None
    estado: str
    estado_codigo: str
    prioridad: str = "Normal"
    dependencia: str | None = None
    inicio: datetime | None = None
    fin: datetime | None = None
    resultado: str | None = None
    error: str | None = None
    executor_type: str


class OperationExecutionOut(BaseModel):
    id: str
    inicio: datetime | None = None
    fin: datetime | None = None
    duracion_ms: int | None = None
    estado: str
    estado_codigo: str
    empleado_ia: str | None = None
    resultado: str | None = None
    error: str | None = None


class OperationApprovalOut(BaseModel):
    id: str
    estado: str
    estado_codigo: str
    accion: str
    responsable: str | None = None
    fecha: datetime
    comentario: str | None = None


class OperationResultOut(BaseModel):
    resumen: str | None = None
    resultado: dict[str, Any] | None = None
    fecha: datetime | None = None
    referencias: list[str] = Field(default_factory=list)
    estado: str


class OperationActivityOut(BaseModel):
    id: str
    tipo: str
    etiqueta: str
    fecha: datetime
    detalle: str | None = None


class OperationDetailOut(OperationItemOut):
    objective: str
    summary: str | None = None
    error: str | None = None
    costo_metadata: dict[str, Any] = Field(default_factory=dict)


class OperationUpdateRequest(BaseModel):
    prioridad: str | None = None
    employee_id: str | None = None
    vencimiento: datetime | None = None
    sin_vencimiento: bool | None = None


class OperationActionRequest(BaseModel):
    comentario: str | None = None
