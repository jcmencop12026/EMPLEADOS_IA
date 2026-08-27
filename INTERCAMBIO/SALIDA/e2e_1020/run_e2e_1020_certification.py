#!/usr/bin/env python3
"""Ejecuta certificación E2E-INTEGRAL-1020 y genera evidencias."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    cmd = [sys.executable, "-m", "pytest", "tests/test_e2e_integral_1020.py", "-v", "--tb=short"]
    env = {**dict(__import__("os").environ), "PYTHONPATH": f"{ROOT / 'backend'}:{ROOT}"}
    proc = subprocess.run(cmd, cwd=ROOT, env=env)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
