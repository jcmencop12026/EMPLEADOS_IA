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
