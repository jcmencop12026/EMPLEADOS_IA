from app.database import SessionLocal
from app.evaluacion_models import EvaluacionExpediente
from app.espacio_externo_models import EntidadEmpresa, EntidadEmpresaAcceso
from app.models import User

db = SessionLocal()
exps = db.query(EvaluacionExpediente).filter(EvaluacionExpediente.entidad_nombre.like('%Clínica Demo Horizonte%')).all()
print('EXPS', [(e.id, e.codigo, e.entidad_nombre, e.estado, e.nivel) for e in exps])
exp_ids = {e.id for e in exps}
ents = db.query(EntidadEmpresa).all()
print('ENTS', [(e.id, e.expediente_id, e.nombre, e.estado_relacion, e.contacto_email) for e in ents if e.expediente_id in exp_ids])
users = {u.id: u for u in db.query(User).all()}
acc = db.query(EntidadEmpresaAcceso).all()
print('ACCESOS', [(a.id, a.entidad_id, users.get(a.user_id).username if users.get(a.user_id) else None, users.get(a.user_id).email if users.get(a.user_id) else None, a.rol_externo, a.activo) for a in acc])
db.close()