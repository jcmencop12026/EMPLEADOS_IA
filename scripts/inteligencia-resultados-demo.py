#!/usr/bin/env python3
"""Semilla demo para recorrido §14 — inteligencia de resultados EIAAX."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

os.environ.setdefault("DATABASE_URL", f"sqlite:///{ROOT}/data/eiaax.db")

from app.database import SessionLocal  # noqa: E402
from app import diagnostic_models  # noqa: F401, E402
from app import opportunity_models  # noqa: F401, E402
from app import baseline_models  # noqa: F401, E402
from app import evaluacion_models  # noqa: F401, E402
from app import resultados_models  # noqa: F401, E402
from app.models import User  # noqa: E402
from app.seed import bootstrap  # noqa: E402
from app.services import baseline_service as baseline_svc  # noqa: E402
from app.services import evaluacion_service as ev_svc  # noqa: E402
from app.services import resultados_service as res_svc  # noqa: E402


def main() -> None:
    db = SessionLocal()
    try:
        bootstrap(db)
        db.commit()
        user = db.query(User).filter(User.username == "admin").first()
        if not user:
            print("Usuario admin no encontrado — ejecute bootstrap primero.")
            return
        org_id, user_id = user.organization_id, user.id
        now = datetime.now(timezone.utc)

        exp = ev_svc.create_expediente(
            db,
            organization_id=org_id,
            user_id=user_id,
            titulo="Demo Inteligencia Resultados D",
            entidad_nombre="IPS Salud Integral",
            necesidad="Reducir glosas y mejorar tiempos de respuesta",
            objetivo="Demostrar ANTES / PROYECTADO / REAL",
            area_proceso="Salud / Facturación",
            nivel="PRELIMINAR",
        )
        db.commit()
        exp_id = exp.id

        lb = baseline_svc.create_linea_base(
            db,
            organization_id=org_id,
            user_id=user_id,
            indicador="tasa_glosas",
            descripcion="Porcentaje de facturas con glosa",
            unidad="%",
            valor_base=19.5,
            fecha_inicio_base=now - timedelta(days=120),
            fecha_fin_base=now - timedelta(days=90),
            impacto_esperado=10.0,
            proceso="Facturación",
        )
        res_svc.sync_indicador_from_linea_base(db, lb.id, org_id)

        ind = res_svc.create_indicador(
            db,
            org_id,
            nombre="Días respuesta glosa",
            unidad="días",
            valor_antes=16.0,
            valor_proyectado=7.0,
            expediente_id=exp_id,
            proceso="Facturación",
            periodo="2026-Q1",
            tipo_analitica="COMPARATIVA",
        )
        pagador = res_svc.add_dimension_nodo(
            db, org_id, ind["id"], codigo="pagador", etiqueta="EPS Contributivo", valor=42, nivel=0
        )
        res_svc.add_dimension_nodo(
            db,
            org_id,
            ind["id"],
            codigo="causal",
            etiqueta="Codificación incorrecta",
            valor=28,
            nivel=1,
            parent_id=pagador["id"],
        )

        res_svc.create_plan_accion(
            db,
            org_id,
            expediente_id=exp_id,
            accion="Capacitación codificación CUPS",
            indicador_id=ind["id"],
            causa="Errores recurrentes en codificación",
        )

        res_svc.register_medicion_real(
            db, ind["id"], org_id, valor_real=9.5, evidencia_ref="informe-marzo-2026.pdf"
        )

        ind2 = res_svc.create_indicador(
            db,
            org_id,
            nombre="Recuperación cartera glosada",
            unidad="%",
            valor_antes=58.0,
            valor_proyectado=82.0,
            expediente_id=exp_id,
        )
        res_svc.register_medicion_real(
            db, ind2["id"], org_id, valor_real=69.0, evidencia_ref="cierre-Q1-2026"
        )

        ind3 = res_svc.create_indicador(
            db,
            org_id,
            nombre="Reducción costo reproceso",
            unidad="COP",
            valor_antes=45000000,
            valor_proyectado=20000000,
            expediente_id=exp_id,
        )

        informe = res_svc.generate_informe_impacto(db, org_id, user_id, expediente_id=exp_id)
        print(f"Demo lista — expediente_id={exp_id}")
        print(f"Informe: {informe['id']} — {informe['titulo']}")
        print(f"URL frontend: /resultados?expediente_id={exp_id}")
        print(f"URL informe: /resultados/informes/{informe['id']}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
