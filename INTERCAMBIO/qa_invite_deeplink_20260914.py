import os
from app.database import SessionLocal
from app.services import espacio_externo_service as svc

ORG='c4cffa31-a964-4da3-b539-6a3a8fd1386e'
ADMIN='41cd3f7b-f18d-46a6-8000-f5e19553cda0'
ENTIDAD='c863a640-7259-49f0-8d77-34ef4cbdf2f2'
EMAIL='jcmencop1@gmail.com'
os.environ['EIAAX_PUBLIC_URL']='https://cookbook-birds-home-sort.trycloudflare.com'
captured={}
svc.request_password_reset=lambda db, email_or_username: 'QA-TOKEN'
def fake_send(db, organization_id, **kwargs):
    captured.update(kwargs)
    return {'estado':'ENVIADA','detalle':'QA_MOCK'}
svc.comm_svc.send_direct_email=fake_send

db=SessionLocal()
try:
    result=svc.invite_external_user(db,ORG,ADMIN,entidad_id=ENTIDAD,email=EMAIL,full_name='Juan Menco')
    body=captured['contenido']
    assert result['correo_estado']=='ENVIADA'
    assert '/activar-acceso?token=QA-TOKEN&next=%2Fmi-espacio&user=jcmencop1%40gmail.com&external=1' in body
    assert 'no envía una contraseña temporal' in body
    assert 'directamente a su espacio de evaluación' in body
    print('QA_INVITE_DEEPLINK_PASS')
finally:
    db.rollback(); db.close()