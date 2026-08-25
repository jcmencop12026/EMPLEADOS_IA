from enum import StrEnum


class FinOpsCategory(StrEnum):
    MODELO_IA = "Modelo IA"
    OCR = "OCR"
    API_EXTERNA = "API externa"
    INTEGRACION = "Integración"
    ALMACENAMIENTO = "Almacenamiento"
    PROCESAMIENTO = "Procesamiento"
    EJECUCION = "Ejecución"
    OTRO = "Otro"


class FinOpsValueType(StrEnum):
    AHORRO_TIEMPO = "Ahorro de tiempo"
    REDUCCION_COSTO = "Reducción de costo"
    INGRESO_GENERADO = "Ingreso generado"
    PERDIDA_EVITADA = "Pérdida evitada"
    PRODUCTIVIDAD = "Productividad"
    OTRO = "Otro"


class FinOpsValueCertainty(StrEnum):
    REAL = "Real"
    ESTIMADO = "Estimado"
    NO_DISPONIBLE = "No disponible"


class FinOpsBudgetScope(StrEnum):
    EMPRESA = "empresa"
    EMPLEADO = "empleado"
    PROCESO = "proceso"


class FinOpsBudgetState(StrEnum):
    NORMAL = "Normal"
    ATENCION = "Atención"
    CERCA_LIMITE = "Cerca del límite"
    LIMITE_ALCANZADO = "Límite alcanzado"


class FinOpsBudgetPolicy(StrEnum):
    SOLO_INFORMAR = "Solo informar"
    REQUIERE_APROBACION = "Requiere aprobación"
    BLOQUEAR = "Bloquear"
