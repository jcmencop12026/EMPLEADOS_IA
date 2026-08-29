#!/usr/bin/env python3
"""Borrado seguro de la organización DEMO EMPLEADOS IA."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.database import SessionLocal
from app.demo_integral.purge import DemoPurgeAbortError, purge_demo_integral


def main() -> int:
    db = SessionLocal()
    try:
        result = purge_demo_integral(db)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return 0
    except DemoPurgeAbortError as exc:
        print(json.dumps({"status": "aborted", "detail": str(exc)}, ensure_ascii=False), file=sys.stderr)
        db.rollback()
        return 2
    except Exception as exc:
        print(json.dumps({"status": "error", "detail": str(exc)}, ensure_ascii=False), file=sys.stderr)
        db.rollback()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
