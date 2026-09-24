from app.database import SessionLocal
from app.espacio_externo_models import EntidadEmpresa
from app.models import User
from app.services.espacio_externo_service import invite_external_user

db=SessionLocal()
try:
    ent=db.query(EntidadEmpresa).filter(EntidadEmpresa.id=='c863a640-7259-49f0-8d77-34ef4cbdf2f2').first()
    admin=db.query(User).filter(User.organization_id==ent.organization_id, User.role.in_(['superadmin','admin','SUPERADMIN','SUPER_ADMIN'])).first()
    if not admin:
        admin=db.query(User).filter(User.organization_id==ent.organization_id, User.is_active.is_(True)).first()
    r=invite_external_user(db, ent.organization_id, admin.id, entidad_id=ent.id, email='jcmencop1@gmail.com', full_name='Gerente Clínica Demo Horizonte', rol_externo='PROSPECTO', password=None)
    db.commit()
    print('INVITE_STATE', r.get('correo_estado'))
    print('INVITE_DETAIL', r.get('correo_detalle'))
    print('PORTAL_URL_OK', bool(r.get('portal_url')))
finally:
    db.close()