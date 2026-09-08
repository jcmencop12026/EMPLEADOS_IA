"""Infraestructura de arranque y mantenimiento de base de datos.

Al importar cualquier módulo de ``scripts`` se registra primero el conjunto completo
 de modelos SQLAlchemy que participa en ``Base.metadata``. Esto evita que las
rutinas de validación/reparación SQLite trabajen con metadata parcial cuando se
invocan antes de ``app.main``.
"""

# Registro centralizado de modelos para validación/reparación de esquema.
# noqa: F401 en todos los imports: el efecto buscado es registrar tablas en Base.metadata.
from app import automation_models  # noqa: F401
from app import baseline_models  # noqa: F401
from app import commercial_models  # noqa: F401
from app import communications_models  # noqa: F401
from app import consumption_planner_models  # noqa: F401
from app import continuidad_comercial_models  # noqa: F401
from app import continuidad_models  # noqa: F401
from app import diagnostic_models  # noqa: F401
from app import economic_motor_models  # noqa: F401
from app import employee_20_models  # noqa: F401
from app import employee_audit_models  # noqa: F401
from app import empresa_seguridad_models  # noqa: F401
from app import espacio_externo_models  # noqa: F401
from app import evaluacion_models  # noqa: F401
from app import experience_models  # noqa: F401
from app import external_models  # noqa: F401
from app import finops_models  # noqa: F401
from app import flujo_comercial_models  # noqa: F401
from app import governance_models  # noqa: F401
from app import gobierno_operacional_models  # noqa: F401
from app import identity_models  # noqa: F401
from app import implementacion_models  # noqa: F401
from app import inteligencia_economica_models  # noqa: F401
from app import integration_models  # noqa: F401
from app import knowledge_models  # noqa: F401
from app import learning_models  # noqa: F401
from app import llm_models  # noqa: F401
from app import models  # noqa: F401
from app import negocio_models  # noqa: F401
from app import opportunity_models  # noqa: F401
from app import optimization_models  # noqa: F401
from app import orchestration_models  # noqa: F401
from app import partner_models  # noqa: F401
from app import presentacion_models  # noqa: F401
from app import resultados_models  # noqa: F401
from app import salud_models  # noqa: F401
from app import scim_models  # noqa: F401
from app import security_models  # noqa: F401
from app import segmentation_models  # noqa: F401
from app import support_models  # noqa: F401
from app import tco_models  # noqa: F401
from app import transformacion_models  # noqa: F401
from app import valuation_models  # noqa: F401