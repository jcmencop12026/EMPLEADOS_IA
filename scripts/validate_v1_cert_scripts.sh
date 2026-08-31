#!/usr/bin/env bash
# Static validation for V1 CERT Windows recovery scripts (Linux CI / cloud agent).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
V1_DIR="$ROOT/INTERCAMBIO/SALIDA/V1_CERT"
PY_SCRIPTS=(
  "$ROOT/backend/scripts/inspect_admin_user.py"
  "$ROOT/backend/scripts/reset_admin_password.py"
)

echo "=== V1 CERT script validation ==="
echo "Root: $ROOT"

fail=0
report() { echo "  FAIL: $1"; fail=1; }
ok() { echo "  OK: $1"; }

# A. PowerShell syntax (pwsh if available)
echo ""
echo "[A] PowerShell syntax"
if command -v pwsh >/dev/null 2>&1; then
  while IFS= read -r -d '' f; do
    if pwsh -NoProfile -Command "\$e=\$null; [void][System.Management.Automation.Language.Parser]::ParseFile('$f', [ref]\$null, [ref]\$e); if (\$e) { exit 1 }" 2>/dev/null; then
      ok "$(basename "$f")"
    else
      report "PowerShell parse: $f"
    fi
  done < <(find "$V1_DIR" -maxdepth 1 -name '*.ps1' -print0 | sort -z)
else
  echo "  SKIP: pwsh not installed (static checks only)"
fi

# B. Python syntax
echo ""
echo "[B] Python syntax"
for f in "${PY_SCRIPTS[@]}"; do
  if python3 -m py_compile "$f" 2>/dev/null; then
    ok "$(basename "$f")"
  else
    report "Python compile: $f"
  fi
done

# C/D. Encoding and corrupt mojibake
echo ""
echo "[C/D] Encoding and corrupt characters"
MOJIBAKE='â€|â€™|â€œ'
python3 - "$ROOT" << 'PY'
import pathlib, sys
root = pathlib.Path(sys.argv[1])
paths = list((root / "INTERCAMBIO/SALIDA/V1_CERT").glob("*.ps1"))
paths += [root / "backend/scripts/inspect_admin_user.py", root / "backend/scripts/reset_admin_password.py"]
fail = False
mojibake = ["\u00e2\u20ac", "\u00e2\u2019", "\u00e2\u20ac\u0153"]
for p in paths:
    text = p.read_text(encoding="utf-8")
    if any(m in text for m in mojibake):
        print(f"  FAIL: Mojibake in {p.name}")
        fail = True
        continue
    if any(ord(c) > 127 for c in text):
        print(f"  FAIL: Non-ASCII in {p.name}")
        fail = True
    else:
        print(f"  OK: ASCII-only: {p.name}")
sys.exit(1 if fail else 0)
PY
if [ $? -ne 0 ]; then fail=1; fi

# E. No fragile python -c inline in executable lines
echo ""
echo "[E] No fragile python -c inline"
for f in "$V1_DIR"/*.ps1; do
  [ -f "$f" ] || continue
  if grep -vE '^\s*#' "$f" | grep -qE '(^|[^a-zA-Z])python(3)?\s+-c\s'; then
    report "python -c invocation in $(basename "$f")"
  else
    ok "no python -c: $(basename "$f")"
  fi
done

# F. Security: no password literals / hash print
echo ""
echo "[F] Security patterns"
for f in "${PY_SCRIPTS[@]}"; do
  if grep -qE 'print\s*\(.*password_hash' "$f"; then
    report "password_hash print in $(basename "$f")"
  else
    ok "no hash leak: $(basename "$f")"
  fi
done

for f in "$V1_DIR"/*.ps1; do
  [ -f "$f" ] || continue
  if grep -qE 'Write-Host\s+.*\$password|password\s*=\s*["'"'"'][^"'"'"']+["'"'"']' "$f"; then
    report "password echo risk in $(basename "$f")"
  fi
done
ok "PS1 password echo scan done"

# G. Required files
echo ""
echo "[G] Required artifacts"
for req in _V1CertCommon.ps1 Inspect-AdminUser.ps1 Reset-AdminPassword.ps1 Test-LoginApi.ps1 PASO1-Recuperar-Admin.ps1 PASO2-Desplegar-Hotfix-Frontend.ps1 docker-compose.frontend-hotfix.yml; do
  if [ -f "$V1_DIR/$req" ]; then ok "$req"; else report "missing $req"; fi
done

# H. Broken inline scripts must be absent
echo ""
echo "[H] Removed fragile inline scripts"
for bad in Inspect-AdminUser-Inline-e8cb853.ps1 Reset-AdminPassword-Inline-e8cb853.ps1; do
  if [ -f "$V1_DIR/$bad" ]; then
    report "still present: $bad"
  else
    ok "removed: $bad"
  fi
done

# I. No fragile docker inspect Go templates in PowerShell
echo ""
echo "[I] No fragile docker inspect -f Go templates"
for f in "$V1_DIR"/*.ps1; do
  [ -f "$f" ] || continue
  if grep -qE 'inspect\s+(-f|--format)\s+["'\'']?\{\{' "$f"; then
    report "docker inspect Go template in $(basename "$f")"
  else
    ok "no docker Go template: $(basename "$f")"
  fi
done

# J. PASO2 self-contained + compose override
echo ""
echo "[J] PASO2 self-contained deploy"
if grep -q '_V1CertCommon.ps1' "$V1_DIR/PASO2-Desplegar-Hotfix-Frontend.ps1"; then
  report "PASO2 still dot-sources _V1CertCommon.ps1"
else
  ok "PASO2 is self-contained"
fi
if [ -f "$V1_DIR/docker-compose.frontend-hotfix.yml" ]; then
  ok "compose override present"
else
  report "missing docker-compose.frontend-hotfix.yml"
fi

echo ""
if [ "$fail" -eq 0 ]; then
  echo "=== VALIDATION: PASS ==="
  exit 0
else
  echo "=== VALIDATION: FAIL ==="
  exit 1
fi
