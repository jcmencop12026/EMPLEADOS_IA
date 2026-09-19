from app.database import SessionLocal
from app.models import Organization
from app.communications_models import CommChannel, CommMessage
from app.services.communications_service import _deliver_channel, email_channel_readiness

db = SessionLocal()
org = db.query(Organization).filter(Organization.name == "Empresa demo").first()
assert org, "ORG_NO_ENCONTRADA"
channel = db.query(CommChannel).filter(
    CommChannel.organization_id == org.id,
    CommChannel.tipo == "CORREO_ELECTRONICO",
    CommChannel.activo.is_(True),
).first()
assert channel, "CANAL_NO_ENCONTRADO"
print("READINESS", email_channel_readiness(db, org.id))
msg = CommMessage(
    organization_id=org.id,
    channel_id=channel.id,
    estado="PENDIENTE_ENVIO",
    tipo_comunicacion="QA",
    destinatario_tipo="EXTERNO",
    destinatario_externo="proauditorx@gmail.com",
    asunto="[EIIAX QA] Ruta general comunicaciones",
    contenido="Prueba de la ruta general de comunicaciones EIIAX.",
)
print("DELIVERY", _deliver_channel(db, msg, channel))
db.close()
