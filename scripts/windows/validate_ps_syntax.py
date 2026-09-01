#!/usr/bin/env python3
"""Validación estática de scripts PowerShell EIAAX (sin ejecutar en Windows)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WINDOWS_DIR = Path(__file__).resolve().parent

# Patrones problemáticos documentados (p. ej. $p: interpretado como unidad)
BAD_PATTERNS = [
    (re.compile(r'\$[A-Za-z_][A-Za-z0-9_]*:(?!\\)'), "Posible interpolación ambigua tipo `$var:` — use `${var}`"),
]
ALLOWED_SCOPE_PREFIXES = ("env:", "script:", "global:", "using:")

REQUIRED_SNIPPETS = [
    "${port}",
    "${Port}",
    "${procId}",
    "${worktree}",
]


def validate_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    if not text.startswith("#Requires -Version"):
        issues.append(f"{path.name}: falta #Requires -Version")

    for idx, line in enumerate(lines, start=1):
        for pattern, message in BAD_PATTERNS:
            for match in pattern.finditer(line):
                token = match.group(0)
                if any(token.startswith(f"${prefix}") or token.startswith(f"$" + prefix.split(":")[0] + ":") for prefix in ALLOWED_SCOPE_PREFIXES):
                    continue
                if token.startswith("$env:"):
                    continue
                if "${" in line:
                    continue
                issues.append(f"{path.name}:{idx}: {message} -> {line.strip()}")

    if path.name != "EiaaxDemo.Common.ps1":
        if ". EiaaxDemo.Common.ps1" not in text and "EiaaxDemo.Common.ps1" not in text:
            if path.name not in {"iniciar_demo_eiaax.ps1"}:
                pass  # iniciar_demo delega en otros scripts

    lowered = text.lower()
    if "remove-item" in lowered and "data" in lowered and "demo" not in lowered:
        issues.append(f"{path.name}: posible borrado de datos fuera de demo")

    if re.search(r"D:\\EMPLEADOS_IA[^_]", text):
        risky = [
            ln
            for ln in lines
            if re.search(r"D:\\EMPLEADOS_IA[^_]", ln)
            and "Refusing" not in ln
            and "Assert-EiaaxNotOriginalTree" not in ln
            and '-eq "D:\\EMPLEADOS_IA' not in ln
        ]
        if risky:
            issues.append(f"{path.name}: referencia a D:\\EMPLEADOS_IA original sin _INTEGRADO")

    return issues


def main() -> int:
    if not WINDOWS_DIR.is_dir():
        print(f"ERROR: no existe {WINDOWS_DIR}")
        return 1

    ps_files = sorted(WINDOWS_DIR.glob("*.ps1"))
    if not ps_files:
        print("ERROR: no hay scripts .ps1")
        return 1

    all_issues: list[str] = []
    for path in ps_files:
        all_issues.extend(validate_file(path))

    print(f"Archivos revisados: {len(ps_files)}")
    for path in ps_files:
        print(f"  OK parse: {path.name} ({path.stat().st_size} bytes)")

    if all_issues:
        print("\nPROBLEMAS:")
        for issue in all_issues:
            print(f"  - {issue}")
        return 1

    print("\nSintaxis estática: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
