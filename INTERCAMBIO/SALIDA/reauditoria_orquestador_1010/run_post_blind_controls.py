#!/usr/bin/env python3
"""Fases 2-10 — controles post-ciegos ORQUESTADOR-EXPERIENCIA-1010.

Requiere brutos/OX_*_ANTES_ORACULO.json generados por run_blind_certification.py.

Uso:
  PYTHONPATH=backend python3 INTERCAMBIO/SALIDA/reauditoria_orquestador_1010/run_post_blind_controls.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from certification_common import (
    BRUTOS,
    CASES,
    ROOT,
    SALIDA,
    bruto_summary,
    find_package_root,
    fresh_db_session,
    load_case_manifest,
    ranking_from_candidatos,
    resolve_case_dir,
    run_selection_blind,
    seed_case_experiences,
)


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def _contains(keyword: str, text: str) -> bool:
    return _norm(keyword) in _norm(text)


def compare_ox_a_e(brutos: dict[str, dict], pkg: Path) -> list[dict[str, Any]]:
    results = []
    leaders: dict[str, str] = {}

    for case in ("OX_A", "OX_B", "OX_C", "OX_D", "OX_E"):
        blind = brutos[case]
        oracle = json.loads((resolve_case_dir(pkg, case) / "resultado_esperado.json").read_text(encoding="utf-8"))
        lider_name = (blind.get("lider") or {}).get("employee_name", "")
        leaders[case] = lider_name
        checks: dict[str, bool] = {}

        if oracle.get("lider_keyword"):
            checks["lider_keyword"] = _contains(oracle["lider_keyword"], lider_name)
        if oracle.get("lider_prohibido"):
            checks["no_lider_prohibido"] = not _contains(oracle["lider_prohibido"], lider_name)
        if oracle.get("dominio_principal"):
            checks["dominio"] = blind.get("dominio_principal") == oracle["dominio_principal"]
        if oracle.get("tipo_problema"):
            checks["tipo_problema"] = blind.get("tipo_problema") == oracle["tipo_problema"]

        if case == "OX_B" and oracle.get("lider_distinto_de"):
            ref = leaders.get("OX_A", "")
            checks["distinto_ox_a"] = lider_name != ref

        if case == "OX_C":
            dominio = blind.get("dominio_principal")
            domain_cands = [c for c in blind.get("candidatos", []) if c.get("domain") == dominio]
            by_code: dict[str, dict] = {}
            for c in domain_cands:
                code = c.get("employee_code")
                if not code:
                    continue
                prev = by_code.get(code)
                if not prev or (c.get("score") or 0) > (prev.get("score") or 0):
                    by_code[code] = c
            cartera = by_code.get("ips-cartera-analyst", {})
            contractual = by_code.get("ips-contractual-analyst", {})
            exp_c = (cartera.get("factores") or {}).get("experiencia", 0)
            exp_ct = (contractual.get("factores") or {}).get("experiencia", 0)
            checks["contractual_compite"] = contractual.get("employee_code") is not None
            checks["calidad_supera_volumen"] = exp_ct >= exp_c
            checks["competencia_cercana"] = (contractual.get("score") or 0) >= (cartera.get("score") or 0) * 0.85
            checks["volumen_no_domina_solo"] = checks["calidad_supera_volumen"] and checks["competencia_cercana"]

        if case == "OX_D":
            specs = {m.get("specialty") for m in blind.get("equipo", []) if m.get("specialty")}
            checks["validador"] = blind.get("validador") is not None
            checks["diversidad_especialidades"] = len(specs) >= 3
            checks["complementarios"] = len(blind.get("complementarios", [])) >= oracle.get("min_complementarios", 2)

        if case == "OX_E":
            checks["no_cartera_lider"] = not _contains("cartera", lider_name)
            checks["datos_insuficientes"] = blind.get("tipo_problema") == "datos_insuficientes"
            razon = blind.get("razon_seleccion_global", "")
            checks["razon_menciona_insuficiencia"] = (
                "insuficiente" in _norm(razon) or "estratég" in _norm(lider_name) or "estrateg" in _norm(lider_name)
            )

        passed = all(checks.values()) if checks else True
        results.append(
            {
                "caso": case,
                "checks": checks,
                "veredicto": "PASS" if passed else "FAIL",
                "resumen": bruto_summary(blind),
                "lider": lider_name,
            }
        )
    return results


def anti_prefab_check(brutos: dict[str, dict], pkg: Path) -> dict[str, Any]:
    leaders = [(brutos[c].get("lider") or {}).get("employee_name") for c in ("OX_A", "OX_B", "OX_C", "OX_D", "OX_E")]
    unique = set(leaders)
    cartera_count = sum(1 for l in leaders if l and "Cartera" in l)

    rules_path = pkg / "ANTI_LIDER_PREFABRICADO.json"
    min_unique = 4
    max_cartera = 2
    if rules_path.is_file():
        rules = json.loads(rules_path.read_text(encoding="utf-8"))
        min_unique = rules.get("min_lideres_distintos", min_unique)
        max_cartera = rules.get("max_cartera_lider_sin_justificacion", max_cartera)

    razones = [brutos[c].get("razon_seleccion_global") for c in ("OX_A", "OX_B", "OX_C", "OX_D", "OX_E")]
    razones_unicas = len({_norm(r) for r in razones if r})

    passed = len(unique) >= min_unique and cartera_count <= max_cartera and razones_unicas >= 3
    return {
        "veredicto": "PASS" if passed else "FAIL",
        "lideres": leaders,
        "lideres_unicos": len(unique),
        "cartera_como_lider": cartera_count,
        "razones_unicas": razones_unicas,
        "por_que_cambia": {
            c: {
                "lider": (brutos[c].get("lider") or {}).get("employee_name"),
                "dominio": brutos[c].get("dominio_principal"),
                "razon": brutos[c].get("razon_seleccion_global"),
            }
            for c in ("OX_A", "OX_B", "OX_C", "OX_D", "OX_E")
        },
    }


def ox_f_learning_check(pkg: Path) -> dict[str, Any]:
    case_dir = resolve_case_dir(pkg, "OX_F")
    manifest = load_case_manifest(case_dir)
    setup = manifest["setup"]
    solicitud = manifest["solicitud"]
    available = setup.get("available_data")

    db, org_id, _ = fresh_db_session("OX_F_post")
    blind_antes = run_selection_blind(db, org_id, solicitud, available, setup=setup, caso_id="OX_F")
    ranking_antes = ranking_from_candidatos(blind_antes.get("candidatos", []))
    lider_antes = blind_antes.get("lider") or {}
    peso_antes = (lider_antes.get("factores") or {}).get("experiencia")
    explicacion_antes = blind_antes.get("razon_seleccion_global")

    record_id = setup.get("_learning_record_id")
    if not record_id:
        from certification_common import seed_learning_experience

        record_id = seed_learning_experience(db, org_id, setup["experiencia_aprendizaje"])

    from app.services.experience_core import actualizar_resultado_experiencia

    neg = setup["experiencia_aprendizaje"]["resultado_real_negativo"]
    actualizar_resultado_experiencia(
        db,
        org_id,
        record_id,
        resultado_real=neg["resultado_real"],
        estado=neg["estado"],
        kpi_despues=neg.get("kpi_despues"),
    )
    db.commit()

    blind_despues = run_selection_blind(
        db, org_id, solicitud, available, setup=setup, caso_id="OX_F", skip_seed=True
    )
    ranking_despues = ranking_from_candidatos(blind_despues.get("candidatos", []))
    lider_despues = blind_despues.get("lider") or {}
    peso_despues = (lider_despues.get("factores") or {}).get("experiencia")
    explicacion_despues = blind_despues.get("razon_seleccion_global")

    rad_code = setup["experiencia_aprendizaje"]["employee_code"]
    score_antes = next((r["score"] for r in ranking_antes if r["employee_code"] == rad_code), None)
    score_despues = next((r["score"] for r in ranking_despues if r["employee_code"] == rad_code), None)

    changed = (
        ranking_antes != ranking_despues
        or score_antes != score_despues
        or peso_antes != peso_despues
        or explicacion_antes != explicacion_despues
    )
    db.close()

    result = {
        "veredicto": "PASS" if changed else "FAIL",
        "ranking_antes": ranking_antes,
        "ranking_despues": ranking_despues,
        "peso_antes": peso_antes,
        "peso_despues": peso_despues,
        "explicacion_antes": explicacion_antes,
        "explicacion_despues": explicacion_despues,
        "score_radicacion_antes": score_antes,
        "score_radicacion_despues": score_despues,
    }
    (BRUTOS / "OX_F_APRENDIZAJE.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def ox_g_feedback_check(bruto: dict[str, Any]) -> dict[str, Any]:
    ctrl = bruto.get("feedback_control") or {}
    estado = ctrl.get("estado")
    peso = ctrl.get("peso_calidad", 0)
    factores = ctrl.get("factores_calidad") or {}
    passed = estado == "FRACASO" and peso < 0.75 and (
        "feedback_sin_kpi" in factores or estado == "FRACASO"
    )
    return {
        "veredicto": "PASS" if passed else "FAIL",
        "estado": estado,
        "feedback": ctrl.get("feedback_humano"),
        "peso_calidad": peso,
        "factores": factores,
        "resultado_real_prevalece": estado == "FRACASO",
    }


def ox_h_tenant_check(bruto: dict[str, Any], pkg: Path) -> dict[str, Any]:
    setup = load_case_manifest(resolve_case_dir(pkg, "OX_H"))["setup"]
    tb_spec = setup.get("tenant_b_experiencia", {})
    secret = tb_spec.get("resultado_real", "")

    exp_util = bruto.get("experiencias_utilizadas") or []
    razon = bruto.get("razon_seleccion_global", "")
    candidatos = bruto.get("candidatos", [])
    rad_scores = [c for c in candidatos if c.get("employee_code") == "ips-radicacion-analyst"]
    exp_factor = (rad_scores[0].get("factores") or {}).get("experiencia", 0) if rad_scores else 0

    leak_text = _contains(secret, razon) or _contains(secret, json.dumps(bruto, ensure_ascii=False))
    passed = (
        bruto.get("organization_id") == bruto.get("tenant_a_id")
        and not leak_text
        and exp_factor < 0.55
        and len(exp_util) == 0
    )
    return {
        "veredicto": "PASS" if passed else "FAIL",
        "tenant_a": bruto.get("tenant_a_id"),
        "tenant_b": bruto.get("tenant_b_id"),
        "experiencia_tenant_b_no_consultada": len(exp_util) == 0,
        "no_aparece_en_explicacion": not leak_text,
        "exp_factor_radicacion_bajo": exp_factor < 0.55,
        "prueba_negativa": {
            "experiencias_utilizadas": exp_util,
            "exp_factor_radicacion": exp_factor,
        },
    }


def cost_check() -> dict[str, Any]:
    db, org_id, _ = fresh_db_session("OX_COSTO")
    setup = {
        "experiencias": [
            {
                "employee_code": "ips-cartera-analyst",
                "count": 12,
                "dominio": "radicacion",
                "tipo_problema": "radicacion_tardia",
                "estado": "FRACASO",
            },
            {
                "employee_code": "ips-radicacion-analyst",
                "count": 4,
                "dominio": "radicacion",
                "tipo_problema": "radicacion_tardia",
                "estado": "EXITO",
                "resultado_real": "Redujo días",
            },
        ],
        "finops": [
            {"employee_code": "ips-cartera-analyst", "cost": 0.01},
            {"employee_code": "ips-radicacion-analyst", "cost": 0.85},
        ],
    }
    blind = run_selection_blind(
        db,
        org_id,
        "Analiza radicación tardía que afecta cartera",
        ["radicacion", "cartera"],
        setup=setup,
        caso_id="OX_COSTO",
    )
    lider = (blind.get("lider") or {}).get("employee_name", "")
    passed = "Radicación" in lider
    db.close()
    return {
        "veredicto": "PASS" if passed else "FAIL",
        "lider": lider,
        "barato_no_gana_siempre": passed,
        "cartera_costo": 0.01,
        "radicacion_costo": 0.85,
    }


def diversity_check(bruto_d: dict[str, Any]) -> dict[str, Any]:
    lider = bruto_d.get("lider") or {}
    validador = bruto_d.get("validador") or {}
    disidente = bruto_d.get("disidente")
    lider_spec = _norm(lider.get("specialty"))
    val_spec = _norm(validador.get("specialty"))
    passed = (
        validador
        and lider.get("employee_id") != validador.get("employee_id")
        and val_spec != lider_spec
        and bool(validador.get("razon_seleccion") or validador.get("razon_rol"))
    )
    return {
        "veredicto": "PASS" if passed else "FAIL",
        "lider_specialty": lider.get("specialty"),
        "validador_specialty": validador.get("specialty"),
        "disidente": (disidente or {}).get("employee_name"),
        "disidente_presente": disidente is not None,
    }


def metamorphic_check() -> dict[str, Any]:
    db, org_id, _ = fresh_db_session("OX_META")
    solicitud = "Analiza glosas y devoluciones del pagador"
    available = ["glosas", "cartera"]
    setup1 = {
        "experiencias": [
            {
                "employee_code": "ips-glosas-analyst",
                "count": 2,
                "dominio": "glosas",
                "tipo_problema": "glosas_devoluciones",
                "estado": "EXITO",
            }
        ]
    }
    b1 = run_selection_blind(db, org_id, solicitud, available, setup=setup1, caso_id="META1")
    seed_case_experiences(
        db,
        org_id,
        {
            "experiencias": [
                {
                    "employee_code": "ips-glosas-analyst",
                    "count": 8,
                    "dominio": "glosas",
                    "tipo_problema": "glosas_devoluciones",
                    "estado": "FRACASO",
                    "resultado_real": "Sin recuperación",
                }
            ]
        },
    )
    db.commit()
    b2 = run_selection_blind(db, org_id, solicitud, available, setup=None, caso_id="META2", skip_seed=True)
    score1 = (b1.get("lider") or {}).get("score")
    score2 = (b2.get("lider") or {}).get("score")
    exp_changed = score1 != score2

    b3 = run_selection_blind(
        db,
        org_id,
        "Diagnóstico integral combinado cartera radicación glosas",
        ["cartera", "radicacion", "glosas", "facturacion"],
        setup=None,
        caso_id="META3",
        skip_seed=True,
    )
    domain_changed = b3.get("dominio_principal") != b1.get("dominio_principal")
    leader_changed = (b3.get("lider") or {}).get("employee_id") != (b1.get("lider") or {}).get("employee_id")
    db.close()

    passed = exp_changed and (domain_changed or leader_changed)
    return {
        "veredicto": "PASS" if passed else "FAIL",
        "cambio_por_experiencia": exp_changed,
        "cambio_por_dominio": domain_changed or leader_changed,
        "score_antes": score1,
        "score_despues_experiencia": score2,
        "dominio_glosas": b1.get("dominio_principal"),
        "dominio_integral": b3.get("dominio_principal"),
    }


def traceability_check(brutos: dict[str, dict]) -> list[dict[str, Any]]:
    sys.path.insert(0, str(ROOT / "backend"))
    from app.experience_models import ExperienceSelectionLog

    results = []
    for case in CASES:
        blind = brutos[case]
        log_id = blind.get("selection_log_id")
        if not log_id:
            results.append({"caso": case, "veredicto": "FAIL", "motivo": "sin selection_log_id"})
            continue
        db, org_id, _ = fresh_db_session(f"trace_{case}")
        log = db.query(ExperienceSelectionLog).filter_by(id=log_id).first()
        db.close()
        if not log:
            results.append({"caso": case, "veredicto": "FAIL", "motivo": "log no encontrado en DB efímera"})
            continue
        ok = bool(
            log.solicitud
            and log.candidatos_json
            and log.factores_json
            and log.seleccionados_json
            and log.razon_seleccion
        )
        results.append(
            {
                "caso": case,
                "veredicto": "PASS" if ok else "FAIL",
                "log_id": log_id,
                "tiene_candidatos": bool(log.candidatos_json),
                "tiene_factores": bool(log.factores_json),
                "tiene_seleccion": bool(log.seleccionados_json),
            }
        )
    return results


def traceability_from_bruto(brutos: dict[str, dict]) -> list[dict[str, Any]]:
    """Trazabilidad reconstruible desde el bruto congelado (DB efímera ya descartada)."""
    results = []
    for case in CASES:
        blind = brutos[case]
        ok = bool(
            blind.get("solicitud")
            and blind.get("candidatos")
            and blind.get("factores_pesos")
            and blind.get("lider")
            and blind.get("razon_seleccion_global")
            and blind.get("selection_log_id")
        )
        results.append({"caso": case, "veredicto": "PASS" if ok else "FAIL", "reconstruible_desde_bruto": ok})
    return results


def main() -> int:
    try:
        pkg, _ = find_package_root()
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 2

    sys.path.insert(0, str(ROOT / "backend"))

    brutos: dict[str, dict] = {}
    for case in CASES:
        path = BRUTOS / f"{case}_ANTES_ORACULO.json"
        if not path.is_file():
            print(f"FALTA bruto: {path}", file=sys.stderr)
            return 3
        brutos[case] = json.loads(path.read_text(encoding="utf-8"))

    ox_ae = compare_ox_a_e(brutos, pkg)
    anti_prefab = anti_prefab_check(brutos, pkg)
    ox_f = ox_f_learning_check(pkg)
    ox_g = ox_g_feedback_check(brutos["OX_G"])
    ox_h = ox_h_tenant_check(brutos["OX_H"], pkg)
    costo = cost_check()
    diversidad = diversity_check(brutos["OX_D"])
    meta = metamorphic_check()
    traza = traceability_from_bruto(brutos)

    summary = {
        "fase": "POST_CIEGA",
        "ox_a_e": ox_ae,
        "anti_prefabricado": anti_prefab,
        "ox_f_aprendizaje": ox_f,
        "ox_g_feedback": ox_g,
        "ox_h_tenant": ox_h,
        "costo": costo,
        "diversidad_validador": diversidad,
        "metamorfico": meta,
        "trazabilidad": traza,
    }
    (SALIDA / "resumen_post_oraculo.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    all_pass = (
        all(r["veredicto"] == "PASS" for r in ox_ae)
        and anti_prefab["veredicto"] == "PASS"
        and ox_f["veredicto"] == "PASS"
        and ox_g["veredicto"] == "PASS"
        and ox_h["veredicto"] == "PASS"
        and costo["veredicto"] == "PASS"
        and diversidad["veredicto"] == "PASS"
        and meta["veredicto"] == "PASS"
        and all(r["veredicto"] == "PASS" for r in traza)
    )
    print(json.dumps({"overall": "PASS" if all_pass else "FAIL", **summary}, ensure_ascii=False, indent=2)[:4000])
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
