#!/usr/bin/env python3
"""Validate EIAAX Windows PowerShell scripts with the real PowerShell parser."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

WINDOWS_DIR = Path(__file__).resolve().parent
PARSE_SCRIPT = WINDOWS_DIR / "validate_ps_parse.ps1"


def ensure_utf8_bom(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if text.startswith("\ufeff"):
        return
    path.write_text("\ufeff" + text.lstrip("\ufeff"), encoding="utf-8")


def main() -> int:
    ps_files = sorted(WINDOWS_DIR.glob("*.ps1"))
    if not ps_files:
        print("ERROR: no PowerShell scripts found")
        return 1

    for path in ps_files:
        ensure_utf8_bom(path)

    if not PARSE_SCRIPT.exists():
        print(f"ERROR: missing {PARSE_SCRIPT}")
        return 1

    result = subprocess.run(
        ["pwsh", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(PARSE_SCRIPT)],
        capture_output=True,
        text=True,
        check=False,
    )
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
