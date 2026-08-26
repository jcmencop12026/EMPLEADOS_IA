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


class WorkPlanPriority(StrEnum):
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    CRITICA = "CRITICA"


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


class EmployeeLifecycleStatus(StrEnum):
    DRAFT = "DRAFT"
    CONFIGURING = "CONFIGURING"
    READY_FOR_TEST = "READY_FOR_TEST"
    TESTING = "TESTING"
    FAILED_TEST = "FAILED_TEST"
    READY_FOR_CERTIFICATION = "READY_FOR_CERTIFICATION"
    CERTIFIED = "CERTIFIED"
    PUBLISHED = "PUBLISHED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    RETIRED = "RETIRED"


class EmployeeMaturity(StrEnum):
    DRAFT = "DRAFT"
    LAB = "LAB"
    SHADOW = "SHADOW"
    SUPERVISED = "SUPERVISED"
    AUTONOMOUS_CONTROLLED = "AUTONOMOUS_CONTROLLED"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ToolPermission(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"


class TestType(StrEnum):
    SMOKE = "SMOKE"
    FUNCTIONAL = "FUNCTIONAL"
    NEGATIVE = "NEGATIVE"
    SECURITY = "SECURITY"
    BOUNDARY = "BOUNDARY"


class CertificationResult(StrEnum):
    PASS = "PASS"
    PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"
    FAIL = "FAIL"


class EmployeeEventType(StrEnum):
    EMPLOYEE_CREATED = "employee.created"
    EMPLOYEE_UPDATED = "employee.updated"
    EMPLOYEE_TESTED = "employee.tested"
    EMPLOYEE_CERTIFIED = "employee.certified"
    EMPLOYEE_CERTIFICATION_FAILED = "employee.certification_failed"
    EMPLOYEE_PUBLISHED = "employee.published"
    EMPLOYEE_ACTIVATED = "employee.activated"
    EMPLOYEE_PAUSED = "employee.paused"
    EMPLOYEE_VERSION_CHANGED = "employee.version_changed"


class AutomationStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    DISABLED = "DISABLED"
    ERROR = "ERROR"


class AutomationTriggerType(StrEnum):
    SCHEDULE = "SCHEDULE"
    MANUAL = "MANUAL"
    INTERNAL_EVENT = "INTERNAL_EVENT"


class ScheduleType(StrEnum):
    ONE_TIME = "ONE_TIME"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    INTERVAL = "INTERVAL"


class AutomationRunStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    SKIPPED = "SKIPPED"


class KnowledgeSourceType(StrEnum):
    TEXT = "TEXT"
    FILE = "FILE"
    URL = "URL"
    DATABASE = "DATABASE"
    API = "API"


class KnowledgeIngestionStatus(StrEnum):
    PENDING = "PENDIENTE"
    PROCESSING = "PROCESANDO"
    COMPLETED = "COMPLETADO"
    FAILED = "FALLIDO"


class TestLabStatus(StrEnum):
    RUNNING = "EJECUTANDO"
    WAITING_APPROVAL = "ESPERANDO_APROBACION"
    COMPLETED = "COMPLETADO"
    FAILED = "FALLIDO"
    BLOCKED = "BLOQUEADO"


class CapabilityEventType(StrEnum):
    CREATED = "capability.created"
    UPDATED = "capability.updated"
    ASSIGNED = "capability.assigned"
    REMOVED = "capability.removed"


class ToolEventType(StrEnum):
    CREATED = "tool.created"
    UPDATED = "tool.updated"
    ASSIGNED = "tool.assigned"
    REMOVED = "tool.removed"
    DENIED = "tool.denied"


class KnowledgeEventType(StrEnum):
    CREATED = "knowledge.created"
    UPDATED = "knowledge.updated"
    ASSIGNED = "knowledge.assigned"
    REMOVED = "knowledge.removed"
    INGESTED = "knowledge.ingested"


class TestLabEventType(StrEnum):
    STARTED = "test_lab.started"
    COMPLETED = "test_lab.completed"
    FAILED = "test_lab.failed"
