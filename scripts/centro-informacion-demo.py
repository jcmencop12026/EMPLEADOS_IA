#!/usr/bin/env python3
"""Demo runtime MB-11 — Centro de Información + entrega de informes."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/mb11-runtime/data/mb11.db")

from app.database import SessionLocal  # noqa: E402
from app import diagnostic_models  # noqa: F401, E402
from app import evaluacion_models  # noqa: F401, E402
from app import resultados_models  # noqa: F401, E402
from app import communications_models  # noqa: F401, E402
from app.models import User  # noqa: E402
from app.seed import bootstrap  # noqa: E402
from app.services import communications_service as comm_svc  # noqa: E402
from app.services import evaluacion_service as ev_svc  # noqa: E402
from app.services import resultados_service as res_svc  # noqa: E402


def main() -> None:
    db = SessionLocal()
    try:
        bootstrap(db)
        db.commit()
        user = db.query(User).filter(User.username == "admin").first()
        assert user
        org_id, user_id = user.organization_id, user.id
        comm_svc.bootstrap_default_comm_assets(db, org_id, user)

        exp = ev_svc.create_expediente(
            db,
            organization_id=org_id,
            user_id=user_id,
            titulo="Demo Centro Información MB-11",
            entidad_nombre="IPS Comunicaciones Demo",
            nivel="PRELIMINAR",
        )
        db.commit()
        informe = res_svc.generate_informe_impacto(db, org_id, user_id, expediente_id=exp.id, visibilidad="VISIBLE_ENTIDAD")
        ch = comm_svc.list_channels(db, org_id)[0]
        entrega = comm_svc.deliver_informe_impacto(
            db, org_id, user, informe_id=informe["id"], channel_id=ch["id"],
            destinatario_tipo="USUARIO", destinatario_id=user_id,
        )
        comm_svc.send_solicitud_informacion_faltante(
            db, org_id, user, expediente_id=exp.id, destinatario_id=user_id, porcentaje=42.0,
        )
        print(f"expediente_id={exp.id}")
        print(f"informe_id={informe['id']}")
        print(f"entrega_message_id={entrega['message']['id']}")
        print("URLs: /comunicaciones | /resultados/informes/" + informe["id"])
    finally:
        db.close()


if __name__ == "__main__":
    main()
