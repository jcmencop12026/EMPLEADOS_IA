#!/usr/bin/env python3
"""Comparación post-oráculo V2 — lee brutos congelados y ORACULO_SELLADO."""

from __future__ import annotations

import csv
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
BRUTOS = BASE / "02_BRUTOS_ANTES_ORACULO"
ORACULO = BASE / "01_PAQUETE" / "ORACULO_SELLADO"
OUT = BASE / "04_COMPARACION_ORACULO"


def _load(case: str) -> tuple[dict, dict]:
    bruto = json.loads((BRUTOS / f"{case}_ANTES_ORACULO.json").read_text(encoding="utf-8"))
    oracle = json.loads((ORACULO / f"{case}_esperado.json").read_text(encoding="utf-8"))
    return bruto, oracle


def eval_case(case: str) -> dict:
    bruto, oracle = _load(case)
    esp = oracle["esperado"]
    obs: dict = {}
    ok = True
    notes: list[str] = []

    def fail(msg: str):
        nonlocal ok
        ok = False
        notes.append(msg)

    if case == "V2-OP-A":
        opp = bruto.get("oportunidad", {})
        pipe = bruto.get("pipeline", {})
        obs = {"momento": opp.get("momento"), "estado": opp.get("estado"), "work_plan_id": opp.get("work_plan_id"),
               "pertinencia": pipe.get("pertinencia"), "autorizacion": (pipe.get("siguiente_accion") or {}).get("autorizacion")}
        if esp.get("momento") and opp.get("momento") != esp["momento"]:
            fail(f"momento esperado {esp['momento']}, observado {opp.get('momento')}")
        if esp.get("debe_crear_plan") and not opp.get("work_plan_id"):
            fail("se esperaba WorkPlan creado")
        if esp.get("requiere_aprobacion") and not pipe.get("capacidad", {}).get("requiere_aprobacion"):
            gate = (pipe.get("siguiente_accion") or {}).get("autorizacion", "")
            if gate not in ("REQUIERE_APROBACION",):
                fail(f"se esperaba aprobación, gate={gate}")
        if esp.get("valor_materializado") is False and float(opp.get("valor_materializado") or 0) > 0:
            fail("valor materializado prematuro")

    elif case == "V2-OP-B":
        created = bruto.get("pipeline", {}).get("opportunity_id") is not None
        pert = bruto.get("pipeline", {}).get("pertinencia")
        momento = bruto.get("oportunidad", {}).get("momento")
        obs = {"oportunidad_creada": created, "pertinencia": pert, "momento": momento}
        if esp.get("es_oportunidad") is False and created:
            fail("señal inmadura generó oportunidad (R02)")
        if esp.get("momento") == "OBSERVAR" and momento == "AHORA":
            fail("momento AHORA cuando debía OBSERVAR")

    elif case == "V2-OP-C":
        opp = bruto.get("oportunidad", {})
        obs = {"momento": opp.get("momento"), "estado": opp.get("estado")}
        if esp.get("momento") and opp.get("momento") != esp["momento"]:
            fail(f"momento esperado {esp['momento']}, observado {opp.get('momento')}")

    elif case == "V2-OP-D":
        ranking = bruto.get("priorizacion_global", {}).get("ranking", [])
        first = ranking[0]["titulo"] if ranking else ""
        obs = {"primero": first, "por_que": bruto.get("decision_final")}
        if esp.get("preferencia") == "D1" and "D1" not in first:
            fail(f"se esperaba preferencia D1, primero={first}")

    elif case == "V2-OP-E":
        opp = bruto.get("oportunidad", {})
        obs = {"pertinencia": opp.get("pertinencia"), "valor_potencial": opp.get("valor_potencial"),
               "certidumbre": opp.get("valor_potencial_certidumbre")}
        if esp.get("debe_inventar_valor") is False and float(opp.get("valor_potencial") or 0) > 0:
            fail("valor inventado sin base")
        if opp.get("pertinencia") not in ("OBSERVAR", "SOLICITAR_DATOS"):
            fail(f"pertinencia inadecuada para datos insuficientes: {opp.get('pertinencia')}")

    elif case == "V2-OP-F":
        opp = bruto.get("oportunidad", {})
        ctx = opp.get("contexto", {})
        obs = {"pertinencia": opp.get("pertinencia"), "momento": opp.get("momento"), "conflicto": ctx.get("conflicto")}
        if esp.get("debe_conservar_contradiccion") and not ctx.get("conflicto"):
            fail("conflicto no conservado")
        if esp.get("momento") == "OBSERVAR" and opp.get("momento") == "AHORA":
            fail("momento AHORA con contradicción")
        if esp.get("debe_crear_plan") is False and opp.get("work_plan_id"):
            fail("plan creado con contradicción")

    elif case.startswith("V2-NS"):
        opp = bruto.get("oportunidad", {})
        obs = {"dominio": opp.get("dominio"), "tipo": opp.get("tipo"), "finops": opp.get("finops_reference")}
        if esp.get("no_depende_salud") and opp.get("dominio") in ("salud", "ips"):
            fail("dependencia SALUD detectada")
        if case == "V2-NS-2" and esp.get("finops_permitido") is False and opp.get("finops_reference"):
            fail("FINOPS registrado sin base")

    elif case == "V2-PX-1":
        obs = {"idempotente": bruto.get("idempotente"), "signals": bruto.get("signal_ids_unicos")}
        if not bruto.get("idempotente"):
            fail("idempotencia no cumplida")

    elif case == "V2-PX-2":
        obs = {"fail_closed": bruto.get("fail_closed"), "contaminacion": bruto.get("contaminacion_tenant_b")}
        if esp.get("acceso_cruzado_permitido") is False and not bruto.get("fail_closed"):
            fail("cross-tenant no fail-closed")

    elif case == "V2-PX-3":
        obs = {"potencial": bruto.get("valor_potencial"), "materializado": bruto.get("valor_materializado"),
               "separados": bruto.get("separados")}
        if esp.get("valor_materializado") is False and float(bruto.get("valor_materializado") or 0) > 0:
            fail("valor materializado sin ejecución")

    elif case == "V2-PX-4":
        etapas = set(bruto.get("etapas", []))
        obs = {"etapas": list(etapas), "experiencias": bruto.get("experiencias_registradas")}
        required = {"SENAL_CREADA", "OPORTUNIDAD_CREADA", "ACTIVACION", "RESULTADO"}
        if esp.get("debe_trazar_cadena_completa") and not required.issubset(etapas):
            fail(f"cadena incompleta, faltan {required - etapas}")
        if esp.get("debe_registrar_aprendizaje") and bruto.get("experiencias_registradas", 0) < 1:
            fail("sin aprendizaje registrado")

    return {
        "caso": case,
        "resultado": "PASS" if ok else "FAIL",
        "esperado": esp,
        "observado": obs,
        "notas": notes,
    }


def eval_r01_r12(results: list[dict]) -> list[dict]:
    by = {r["caso"]: r for r in results}
    rows = []

    def row(ctrl, casos, esperado, obs, res, nota=""):
        rows.append({"control": ctrl, "casos": casos, "esperado": esperado, "observado": obs,
                     "resultado": res, "observacion": nota})

    row("R01", "V2-PX-1", "proactividad/idempotencia", by["V2-PX-1"]["observado"],
        by["V2-PX-1"]["resultado"], ";".join(by["V2-PX-1"]["notas"]))
    row("R02", "V2-OP-B", "señal≠oportunidad", by["V2-OP-B"]["observado"],
        by["V2-OP-B"]["resultado"], ";".join(by["V2-OP-B"]["notas"]))
    row("R03", "V2-OP-D", "priorización global D1", by["V2-OP-D"]["observado"],
        by["V2-OP-D"]["resultado"], ";".join(by["V2-OP-D"]["notas"]))
    row("R04", "V2-OP-C,V2-OP-F", "momento PROGRAMAR/OBSERVAR",
        f"C={by['V2-OP-C']['resultado']} F={by['V2-OP-F']['resultado']}",
        "PASS" if by["V2-OP-C"]["resultado"] == "PASS" and by["V2-OP-F"]["resultado"] == "PASS" else "FAIL")
    row("R05", "V2-OP-E,V2-NS-2", "no inventar valor",
        f"E={by['V2-OP-E']['resultado']} NS2={by['V2-NS-2']['resultado']}",
        "PASS" if by["V2-OP-E"]["resultado"] == "PASS" and by["V2-NS-2"]["resultado"] == "PASS" else "FAIL")
    row("R06", "V2-OP-F", "contradicción", by["V2-OP-F"]["observado"],
        by["V2-OP-F"]["resultado"], ";".join(by["V2-OP-F"]["notas"]))
    row("R07", "V2-NS-1,V2-NS-2", "transversalidad",
        f"NS1={by['V2-NS-1']['resultado']} NS2={by['V2-NS-2']['resultado']}",
        "PASS" if by["V2-NS-1"]["resultado"] == "PASS" and by["V2-NS-2"]["resultado"] == "PASS" else "FAIL")
    row("R08", "V2-PX-1", "idempotencia", by["V2-PX-1"]["observado"],
        by["V2-PX-1"]["resultado"])
    row("R09", "V2-PX-3", "potencial≠materializado", by["V2-PX-3"]["observado"],
        by["V2-PX-3"]["resultado"])
    row("R10", "V2-PX-2", "cross-tenant", by["V2-PX-2"]["observado"],
        by["V2-PX-2"]["resultado"])
    row("R11", "V2-OP-A", "NBA+plan", by["V2-OP-A"]["observado"],
        by["V2-OP-A"]["resultado"], ";".join(by["V2-OP-A"]["notas"]))
    row("R12", "V2-PX-4", "trazabilidad", by["V2-PX-4"]["observado"],
        by["V2-PX-4"]["resultado"])
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cases = [f"V2-OP-{c}" for c in "ABCDEF"] + ["V2-NS-1", "V2-NS-2"] + [f"V2-PX-{i}" for i in range(1, 5)]
    results = [eval_case(c) for c in cases]
    (OUT / "RESULTADOS_CASOS.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    r_rows = eval_r01_r12(results)
    with (OUT / "RESULTADOS_R01_R12.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["control", "casos", "esperado", "observado", "resultado", "observacion"])
        w.writeheader()
        w.writerows(r_rows)
    fails = [r for r in results if r["resultado"] == "FAIL"] + [r for r in r_rows if r["resultado"] == "FAIL"]
    print(json.dumps({"casos_fail": len([r for r in results if r["resultado"] == "FAIL"]),
                      "r_fail": len([r for r in r_rows if r["resultado"] == "FAIL"]),
                      "veredicto": "PASS" if not fails else "FAIL"}, indent=2))


if __name__ == "__main__":
    main()
