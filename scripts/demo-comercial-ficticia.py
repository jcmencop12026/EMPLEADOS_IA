#!/usr/bin/env python3
"""Semilla unificada — Demo comercial ficticia EIAAX (V1)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

os.environ.setdefault("DATABASE_URL", f"sqlite:///{ROOT}/data/eiaax.db")

from app.database import SessionLocal  # noqa: E402
from app import evaluacion_models  # noqa: F401, E402
from app import resultados_models  # noqa: F401, E402
from app import baseline_models  # noqa: F401, E402
from app.models import User  # noqa: E402
from app.seed import bootstrap  # noqa: E402
from app.services import demo_comercial_service as demo_svc  # noqa: E402


def main() -> None:
    db = SessionLocal()
    try:
        bootstrap(db)
        db.commit()
        user = db.query(User).filter(User.username == "admin").first()
        if not user:
            print("Usuario admin no encontrado.")
            return
        manifest = demo_svc.seed_demo_comercial(db, user.organization_id, user.id)
        db.commit()
        print("Demo comercial lista — DEMO — DATOS SIMULADOS")
        print(f"Expediente: {manifest.get('expediente_codigo')} ({manifest.get('expediente_id')})")
        print(f"Informe: {manifest.get('informe_id')}")
        enlaces = manifest.get("enlaces") or {}
        print(f"Hub: {enlaces.get('hub')}")
        print(f"Presentación: {enlaces.get('presentacion')}")
        print(f"Evaluación real: {enlaces.get('evaluar_real')}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
