import app.main
from app.database import SessionLocal
from app.models import User

db=SessionLocal()
for email in ['jcmencop2021@gmail.com','jcmencop1@gmail.com']:
    rows=db.query(User).filter((User.email==email)|(User.username==email)).all()
    print(email, [(u.id,u.username,u.email,u.role,u.status,u.is_active,u.organization_id) for u in rows])
db.close()