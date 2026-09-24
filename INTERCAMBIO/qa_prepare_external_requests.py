import app.main  # carga todos los modelos/mappers
from app.database import SessionLocal
from app.evaluacion_models import EvaluacionExpediente
from app.espacio_externo_models import EntidadEmpresa, EntidadEmpresaAcceso
from app.models import User
from app.services import flujo_comercial_service as flujo
from app.services import espacio_externo_service as externo

db=SessionLocal()
exp=db.query(EvaluacionExpediente).filter(EvaluacionExpediente.codigo=='EVA-2026-0001').first()
assert exp, 'expediente demo no encontrado'
admin=db.query(User).filter(User.organization_id==exp.organization_id, User.username=='admin').first()
assert admin, 'admin no encontrado'
items=flujo.sync_informacion_contextual(db, exp, user_id=admin.id)
ent=db.query(EntidadEmpresa).filter(EntidadEmpresa.expediente_id==exp.id).first()
assert ent, 'entidad externa no encontrada'
created=[]
for i in items:
    if i.obligatorio and i.estado in ('PENDIENTE','INCOMPLETO'):
        r=externo.crear_solicitud_informacion(db, exp.organization_id, admin.id, ent.id, titulo=i.etiqueta, descripcion=i.explicacion, informacion_item_id=i.id)
        created.append((i.campo,i.etiqueta,r.get('estado'),r.get('reused',False)))
db.commit()
acc=db.query(EntidadEmpresaAcceso).filter(EntidadEmpresaAcceso.entidad_id==ent.id, EntidadEmpresaAcceso.activo.is_(True)).first()
usr=db.query(User).filter(User.id==acc.user_id).first() if acc else None
portal=externo.get_portal_informacion(db, usr) if usr else {'solicitudes':[],'entregas':[]}
print('REQUISITOS',[(i.campo,i.etiqueta,i.obligatorio,i.estado) for i in items])
print('SOLICITUDES_CREADAS',created)
print('PORTAL_USER',usr.username if usr else None)
print('PORTAL_SOLICITUDES',[(x['etiqueta'],x['estado'],x['puede_entregar']) for x in portal['solicitudes']])
print('PORTAL_ENTREGAS',[(x.get('titulo'),x.get('estado')) for x in portal['entregas']])
db.close()