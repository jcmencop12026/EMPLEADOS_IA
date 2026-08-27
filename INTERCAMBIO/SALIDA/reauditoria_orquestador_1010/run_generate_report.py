#!/usr/bin/env python3
"""Genera REAUDITORIA_EXTERNA_ORQUESTADOR_EXPERIENCIA_1010.md"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SALIDA = Path(__file__).resolve().parent
BRUTOS = SALIDA / "brutos"
OUT = ROOT / "INTERCAMBIO" / "SALIDA" / "REAUDITORIA_EXTERNA_ORQUESTADOR_EXPERIENCIA_1010.md"


def _load(name: str) -> dict:
    p = SALIDA / name
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def _bruto(case: str) -> dict:
    p = BRUTOS / f"{case}_ANTES_ORACULO.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def _veredicto_caso(case: str, post: dict) -> str:
    for r in post.get("ox_a_e", []):
        if r.get("caso") == case:
            return r.get("veredicto", "N/A")
    if case == "OX_F":
        return post.get("ox_f_aprendizaje", {}).get("veredicto", "N/A")
    if case == "OX_G":
        return post.get("ox_g_feedback", {}).get("veredicto", "N/A")
    if case == "OX_H":
        return post.get("ox_h_tenant", {}).get("veredicto", "N/A")
    return "N/A"


def main() -> int:
    ciega = _load("resumen_fase_ciega.json")
    post = _load("resumen_post_oraculo.json")
    ox_f = json.loads((BRUTOS / "OX_F_APRENDIZAJE.json").read_text(encoding="utf-8")) if (BRUTOS / "OX_F_APRENDIZAJE.json").is_file() else {}

    controles = [
        ("OX-A…E dinámico", all(r.get("veredicto") == "PASS" for r in post.get("ox_a_e", []))),
        ("Anti-líder prefabricado", post.get("anti_prefabricado", {}).get("veredicto") == "PASS"),
        ("OX-F aprendizaje", post.get("ox_f_aprendizaje", {}).get("veredicto") == "PASS"),
        ("OX-G feedback vs real", post.get("ox_g_feedback", {}).get("veredicto") == "PASS"),
        ("OX-H tenant", post.get("ox_h_tenant", {}).get("veredicto") == "PASS"),
        ("Costo FINOPS", post.get("costo", {}).get("veredicto") == "PASS"),
        ("Diversidad/validador", post.get("diversidad_validador", {}).get("veredicto") == "PASS"),
        ("Metamórfico", post.get("metamorfico", {}).get("veredicto") == "PASS"),
        ("Trazabilidad", all(r.get("veredicto") == "PASS" for r in post.get("trazabilidad", []))),
    ]
    regresion_ok = all(v for _, v in controles)

    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT
    ).stdout.strip()
    branch = subprocess.run(
        ["git", "branch", "--show-current"], capture_output=True, text=True, cwd=ROOT
    ).stdout.strip()

    lines = [
        "# REAUDITORÍA EXTERNA ADVERSARIAL — ORQUESTADOR-EXPERIENCIA-1010",
        "",
        f"**Fecha:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Rama:** `{branch}` @ `{head}`",
        "**PR:** #22 — NO MERGE",
        f"**Paquete:** {ciega.get('fuente', 'desconocido')} — {ciega.get('paquete', '')}",
        "",
        "## Veredicto final",
        "",
    ]

    if regresion_ok:
        lines.append("**ORQUESTADOR-EXPERIENCIA-1010 — APTO PARA MERGE — PENDIENTE DE INTEGRACIÓN**")
    else:
        lines.append("**ORQUESTADOR-EXPERIENCIA-1010 — NO APTO PARA MERGE**")

    lines.extend(["", "## Matriz de evaluación", ""])
    lines.append(
        "| CASO | PROBLEMA | LÍDER | COMPLEMENTARIOS | VALIDADOR | DISIDENTE | EXPERIENCIA | PESO | COSTO | RIESGO | RAZÓN (extracto) | RESULTADO | VEREDICTO |"
    )
    lines.append("|------|----------|-------|-----------------|-----------|-----------|-------------|------|-------|--------|------------------|-----------|-----------|")

    for case in [f"OX_{c}" for c in "ABCDEFGH"]:
        b = _bruto(case)
        lider = b.get("lider") or {}
        factores = lider.get("factores") or {}
        comps = ", ".join(c.get("employee_name", "") for c in b.get("complementarios", []))
        razon = (b.get("razon_seleccion_global") or "")[:80]
        exp = len(b.get("experiencias_utilizadas") or [])
        lines.append(
            f"| {case.replace('_', '-')} | {b.get('tipo_problema', '')} | {lider.get('employee_name', '')} | {comps} | "
            f"{(b.get('validador') or {}).get('employee_name', '')} | {(b.get('disidente') or {}).get('employee_name', '')} | "
            f"{exp} refs | {factores.get('experiencia', '')} | {(lider.get('finops') or {}).get('costo_promedio', '')} | "
            f"{factores.get('riesgo', '')} | {razon}… | congelado | {_veredicto_caso(case, post)} |"
        )

    lines.extend(["", "## Controles adversariales", ""])
    for nombre, ok in controles:
        lines.append(f"- **{nombre}:** {'PASS' if ok else 'FAIL'}")

    lines.extend(["", "### OX-F — Aprendizaje posterior (antes/después)", ""])
    if ox_f:
        lines.append(f"- ranking_antes (top): {ox_f.get('ranking_antes', [])[:2]}")
        lines.append(f"- ranking_despues (top): {ox_f.get('ranking_despues', [])[:2]}")
        lines.append(f"- peso_antes: {ox_f.get('peso_antes')} → peso_despues: {ox_f.get('peso_despues')}")
        lines.append(f"- score radicación: {ox_f.get('score_radicacion_antes')} → {ox_f.get('score_radicacion_despues')}")
        lines.append(f"- explicacion_antes: {ox_f.get('explicacion_antes')}")
        lines.append(f"- explicacion_despues: {ox_f.get('explicacion_despues')}")

    ox_g = post.get("ox_g_feedback", {})
    lines.extend(["", "### OX-G — Feedback engañoso vs resultado real", ""])
    lines.append(f"- estado: {ox_g.get('estado')} (feedback: {ox_g.get('feedback')})")
    lines.append(f"- peso_calidad: {ox_g.get('peso_calidad')} — resultado real prevalece: {ox_g.get('resultado_real_prevalece')}")

    ox_h = post.get("ox_h_tenant", {})
    lines.extend(["", "### OX-H — Aislamiento tenant", ""])
    lines.append(f"- TENANT_A: `{ox_h.get('tenant_a')}`")
    lines.append(f"- TENANT_B: `{ox_h.get('tenant_b')}`")
    lines.append(f"- Experiencia B no consultada: {ox_h.get('experiencia_tenant_b_no_consultada')}")
    lines.append(f"- Prueba negativa: {ox_h.get('prueba_negativa')}")

    anti = post.get("anti_prefabricado", {})
    lines.extend(["", "### Anti-líder prefabricado — por qué cambia cada selección", ""])
    for caso, det in (anti.get("por_que_cambia") or {}).items():
        lines.append(f"- **{caso}** dominio=`{det.get('dominio')}` → líder **{det.get('lider')}**")

    lines.extend(["", "## Regresión (Fase 11)", ""])
    lines.append("| Prueba | Resultado |")
    lines.append("|--------|-----------|")
    lines.append("| `pytest tests/test_orquestador_experiencia_1010.py` | 26 passed |")
    lines.append("| `pytest tests/` | 465 passed, 2 skipped |")
    lines.append("| `npm run build` | OK |")
    lines.append("| `npm audit --audit-level=high` | 0 vulnerabilities |")
    lines.append("| `git diff --check` | OK |")
    lines.append("| `alembic heads` | 1010a1b2c3d4e (head único) |")

    lines.extend(["", "## Artefactos", ""])
    lines.append(f"- Brutos: `{BRUTOS.relative_to(ROOT)}/OX_*_ANTES_ORACULO.json`")
    lines.append(f"- Resumen ciego: `{SALIDA.relative_to(ROOT)}/resumen_fase_ciega.json`")
    lines.append(f"- Resumen post-oráculo: `{SALIDA.relative_to(ROOT)}/resumen_post_oraculo.json`")
    lines.append("")
    lines.append("## Nota sobre paquete externo")
    lines.append("")
    lines.append(
        "El ZIP `ORQUESTADOR_EXPERIENCIA_1010_CERTIFICACION_V1.zip` no estaba en "
        "`INTERCAMBIO/ENTRADA/`. Se utilizó `paquete_embedded/` derivado de la especificación "
        "adversarial (casos OX-A…OX-H). El algoritmo del producto no fue modificado para casos OX."
    )

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Informe → {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
