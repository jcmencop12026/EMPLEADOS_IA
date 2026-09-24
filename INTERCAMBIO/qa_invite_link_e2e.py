import json, re, time, urllib.request
from app.database import SessionLocal
from app.espacio_externo_models import EntidadEmpresa, EntidadEmpresaAcceso
from app.models import User
from app.services import espacio_externo_service as svc

PUBLIC='https://clothing-librarian-sight-consistent.trycloudflare.com'
ENTITY_ID='c863a640-7259-49f0-8d77-34ef4cbdf2f2'
qa_email=f'qa.invite.{int(time.time())}@example.test'
qa_password='QaLink!2026#OK'
captured={}
orig_send=svc.comm_svc.send_direct_email

def fake_send(*args, **kwargs):
    captured['contenido']=kwargs.get('contenido','')
    captured['destinatario']=kwargs.get('destinatario','')
    return {'estado':'ENVIADA','detalle':'QA_CAPTURE'}
db=SessionLocal()
try:
    ent=db.query(EntidadEmpresa).filter(EntidadEmpresa.id==ENTITY_ID).first()
    assert ent, 'Entidad QA no encontrada'
    old_contact=ent.contacto_email
    admin=db.query(User).filter(User.organization_id==ent.organization_id, User.is_active.is_(True)).first()
    assert admin, 'Admin no encontrado'
    svc.comm_svc.send_direct_email=fake_send
    result=svc.invite_external_user(db, ent.organization_id, admin.id,
        entidad_id=ent.id, email=qa_email, full_name='QA Gerente', rol_externo='PROSPECTO', password=None)
    db.commit()
    body=captured.get('contenido','')
    match=re.search(r'https://[^\s]+/activar-acceso\?token=[^\s]+', body)
    assert match, 'No se generó enlace de activación'
    link=match.group(0)
    print('INVITE', result.get('correo_estado'), result.get('portal_url'))
    print('LINK_HOST_OK', link.startswith(PUBLIC+'/activar-acceso?token='))
    with urllib.request.urlopen(link, timeout=20) as r:
        html=r.read(300).decode(errors='ignore')
        print('PUBLIC_LINK_HTTP', r.status, 'EIIAX' in html or 'DOCTYPE' in html)
    token=link.split('token=',1)[1]
    def post_json(url, payload):
        req=urllib.request.Request(url, data=json.dumps(payload).encode(),
            headers={'Content-Type':'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.loads(r.read().decode())
    st_reset,_=post_json(PUBLIC+'/api/auth/reset-password', {'token':token,'new_password':qa_password})
    print('RESET_HTTP', st_reset)
    st_login,login=post_json(PUBLIC+'/api/auth/login', {'username':qa_email,'password':qa_password})
    print('LOGIN_HTTP', st_login, bool(login.get('access_token')))
    qa_user=db.query(User).filter(User.username==qa_email).first()
    if qa_user:
        db.query(EntidadEmpresaAcceso).filter(EntidadEmpresaAcceso.user_id==qa_user.id).delete()
        qa_user.is_active=False; qa_user.status='INACTIVE'
    ent.contacto_email=old_contact
    db.commit()
    print('CLEANUP_OK', True)
finally:
    svc.comm_svc.send_direct_email=orig_send
    db.close()
