"""NX06 — Smoke post-merge: conftest importa modelos 1100–1380 + MB."""

from __future__ import annotations

from pathlib import Path

import pytest

CONFTEST = Path(__file__).resolve().parent / "conftest.py"

REQUIRED_MODEL_IMPORTS = [
    "opportunity_models",  # 1100
    "finops_models",  # 1110
    "baseline_models",  # 1200
    "valuation_models",  # 1210
    "diagnostic_models",  # 1220
    "learning_models",  # 1260
    "optimization_models",  # 1290
    "segmentation_models",  # 1310
    "tco_models",  # 1320
    "integration_models",  # 1330
    "implementacion_models",  # 1340
    "governance_models",  # 1350
    "continuidad_models",  # 1360
    "identity_models",  # 1370
    "scim_models",  # 1380
    "employee_audit_models",  # MB auditor
    "consumption_planner_models",  # MB-07
    "communications_models",  # MB-11
]


def test_nx06_conftest_imports_phase2_and_mb_models():
    src = CONFTEST.read_text(encoding="utf-8")
    missing = [mod for mod in REQUIRED_MODEL_IMPORTS if f"app import {mod}" not in src and f"app.{mod}" not in src]
    assert not missing, f"conftest.py sin imports: {missing}"
