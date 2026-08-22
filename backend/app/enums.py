from enum import StrEnum


class WorkPlanStatus(StrEnum):
    CREATED = "CREATED"
    PLANNING = "PLANNING"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING_DATA = "WAITING_DATA"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class EmployeeTaskStatus(StrEnum):
    CREATED = "CREATED"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING_DATA = "WAITING_DATA"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class EmployeeStatus(StrEnum):
    DISPONIBLE = "DISPONIBLE"
    PLANIFICANDO = "PLANIFICANDO"
    TRABAJANDO = "TRABAJANDO"
    ESPERANDO_DATOS = "ESPERANDO_DATOS"
    ESPERANDO_APROBACION = "ESPERANDO_APROBACION"
    PAUSADO = "PAUSADO"
    ERROR = "ERROR"
    FINALIZADO = "FINALIZADO"


class ExecutorType(StrEnum):
    RULE = "RULE"
    PYTHON = "PYTHON"
    SQL = "SQL"
    TOOL = "TOOL"
    AUTOMATION = "AUTOMATION"
    AI_AGENT = "AI_AGENT"
    HUMAN = "HUMAN"
    HYBRID = "HYBRID"


class ApprovalStatus(StrEnum):
    NOT_REQUIRED = "NOT_REQUIRED"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class WorkEventType(StrEnum):
    WORK_REQUESTED = "work.requested"
    WORK_PLANNED = "work.planned"
    TASK_CREATED = "task.created"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    APPROVAL_REQUIRED = "approval.required"
    APPROVAL_COMPLETED = "approval.completed"
    WORK_COMPLETED = "work.completed"
    WORK_FAILED = "work.failed"
