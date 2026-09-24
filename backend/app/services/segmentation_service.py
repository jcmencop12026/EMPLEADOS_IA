"""Servicio — Segmentación, paquetes y recomendación (1310)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.commercial_models import CommercialPlan
from app.segmentation_enums import CatalogLifecycle, DiscountType, PlanFitLevel, ScaleDirection
from app.segmentation_models import (
    CommercialCapability,
    CommercialDiscount,
    CommercialPackage,
    CommercialPackageVersion,
    CommercialPlanVersion,
    CommercialSector,
    CommercialSegment,
    OrganizationCommercialProfile,
)
from app.services.commercial_service import _compute_economics, _decimal, get_plan
from app.tenant_scope import ORG_STATUS_ACTIVE
from app.models import Organization


class SegmentationValidationError(ValueError):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, default=str)


def _parse_json(raw: str | None) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _ensure_org_active(db: Session, organization_id: str) -> Organization:
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    if org.status != ORG_STATUS_ACTIVE:
        raise HTTPException(status_code=403, detail="La empresa está inactiva")
    return org


def _sector_to_dict(row: CommercialSector) -> dict[str, Any]:
    return {
        "id": row.id, "code": row.code, "name": row.name, "descripcion": row.descripcion,
        "lifecycle_status": row.lifecycle_status, "organization_id": row.organization_id, "is_active": row.is_active,
    }


def _segment_to_dict(row: CommercialSegment) -> dict[str, Any]:
    return {
        "id": row.id, "code": row.code, "name": row.name, "descripcion": row.descripcion,
        "sector_id": row.sector_id, "dimensions": _parse_json(row.dimensions_json),
        "lifecycle_status": row.lifecycle_status, "organization_id": row.organization_id,
    }


def _package_to_dict(row: CommercialPackage) -> dict[str, Any]:
    return {
        "id": row.id, "code": row.code, "name": row.name, "descripcion": row.descripcion,
        "plan_id": row.plan_id, "segment_id": row.segment_id, "sector_id": row.sector_id,
        "version_number": row.version_number, "lifecycle_status": row.lifecycle_status,
        "is_custom": row.is_custom, "organization_id": row.organization_id,
        "empleados_ia_incluidos": row.empleados_ia_incluidos, "usuarios_incluidos": row.usuarios_incluidos,
        "automatizaciones_incluidas": row.automatizaciones_incluidas,
        "consumo_ia_incluido_tokens": row.consumo_ia_incluido_tokens,
        "presupuesto_ia_incluido": float(row.presupuesto_ia_incluido) if row.presupuesto_ia_incluido else None,
        "integraciones_incluidas": row.integraciones_incluidas, "almacenamiento_gb": row.almacenamiento_gb,
        "sla_nivel": row.sla_nivel, "soporte_nivel": row.soporte_nivel,
        "excedente_ia_por_millon": float(row.excedente_ia_por_millon) if row.excedente_ia_por_millon else None,
        "alerta_consumo_pct": float(row.alerta_consumo_pct) if row.alerta_consumo_pct else None,
        "bloqueo_excedente": row.bloqueo_excedente,
        "credential_modes": _parse_json(row.credential_modes_json),
        "capabilities": _parse_json(row.capabilities_json),
        "servicios_incluidos": _parse_json(row.servicios_incluidos_json),
        "servicios_opcionales": _parse_json(row.servicios_opcionales_json),
        "custom_overrides": _parse_json(row.custom_overrides_json),
        "precio_estimado": float(row.precio_estimado) if row.precio_estimado else None,
    }


def _profile_to_dict(row: OrganizationCommercialProfile) -> dict[str, Any]:
    return {
        "id": row.id, "organization_id": row.organization_id, "segment_id": row.segment_id,
        "sector_id": row.sector_id, "subsector": row.subsector, "tamano": row.tamano,
        "madurez_digital": row.madurez_digital, "complejidad_operativa": row.complejidad_operativa,
        "num_usuarios": row.num_usuarios, "num_empleados_ia": row.num_empleados_ia,
        "volumen_operaciones": row.volumen_operaciones, "num_integraciones": row.num_integraciones,
        "consumo_ia_estimado": row.consumo_ia_estimado, "nivel_soporte": row.nivel_soporte,
        "sla_requerido": row.sla_requerido, "riesgo": row.riesgo,
        "potencial_valor": float(row.potencial_valor) if row.potencial_valor else None,
        "presupuesto_estimado": float(row.presupuesto_estimado) if row.presupuesto_estimado else None,
        "observaciones": row.observaciones,
        "evaluado_en": row.evaluado_en.isoformat() if row.evaluado_en else None,
    }


def create_sector(db: Session, organization_id: str | None, data: dict[str, Any], user_id: str | None) -> CommercialSector:
    row = CommercialSector(
        organization_id=organization_id,
        code=str(data["code"]).strip().lower(),
        name=data["name"],
        descripcion=data.get("descripcion"),
        lifecycle_status=data.get("lifecycle_status", CatalogLifecycle.ACTIVO),
    )
    db.add(row)
    db.flush()
    write_audit(db, action="segmentacion.sector.creado", organization_id=organization_id, user_id=user_id,
                detail=_json({"sector_id": row.id}), commit=False)
    return row


def list_sectors(db: Session, organization_id: str) -> list[CommercialSector]:
    return (
        db.query(CommercialSector)
        .filter(
            (CommercialSector.organization_id == organization_id) | (CommercialSector.organization_id.is_(None)),
            CommercialSector.is_active.is_(True),
        )
        .order_by(CommercialSector.name)
        .all()
    )


def create_segment(db: Session, organization_id: str | None, data: dict[str, Any], user_id: str | None) -> CommercialSegment:
    row = CommercialSegment(
        organization_id=organization_id,
        sector_id=data.get("sector_id"),
        code=str(data["code"]).strip().lower(),
        name=data["name"],
        descripcion=data.get("descripcion"),
        dimensions_json=_json(data.get("dimensions")) if data.get("dimensions") else None,
        lifecycle_status=data.get("lifecycle_status", CatalogLifecycle.ACTIVO),
    )
    db.add(row)
    db.flush()
    write_audit(db, action="segmentacion.segmento.creado", organization_id=organization_id, user_id=user_id,
                detail=_json({"segment_id": row.id}), commit=False)
    return row


def list_segments(db: Session, organization_id: str) -> list[CommercialSegment]:
    return (
        db.query(CommercialSegment)
        .filter(
            (CommercialSegment.organization_id == organization_id) | (CommercialSegment.organization_id.is_(None)),
            CommercialSegment.is_active.is_(True),
        )
        .order_by(CommercialSegment.name)
        .all()
    )


def upsert_profile(db: Session, organization_id: str, data: dict[str, Any], user_id: str | None) -> OrganizationCommercialProfile:
    _ensure_org_active(db, organization_id)
    row = db.query(OrganizationCommercialProfile).filter(OrganizationCommercialProfile.organization_id == organization_id).first()
    if not row:
        row = OrganizationCommercialProfile(organization_id=organization_id)
        db.add(row)
    for field in (
        "segment_id", "sector_id", "subsector", "tamano", "madurez_digital", "complejidad_operativa",
        "num_usuarios", "num_empleados_ia", "volumen_operaciones", "num_integraciones", "consumo_ia_estimado",
        "nivel_soporte", "sla_requerido", "riesgo", "observaciones",
    ):
        if field in data:
            setattr(row, field, data[field])
    if "potencial_valor" in data:
        row.potencial_valor = _decimal(data["potencial_valor"])
    if "presupuesto_estimado" in data:
        row.presupuesto_estimado = _decimal(data["presupuesto_estimado"])
    row.evaluado_en = _utcnow()
    db.flush()
    write_audit(db, action="segmentacion.perfil.actualizado", organization_id=organization_id, user_id=user_id,
                detail=_json({"profile_id": row.id}), commit=False)
    return row


def get_profile(db: Session, organization_id: str) -> OrganizationCommercialProfile | None:
    return db.query(OrganizationCommercialProfile).filter(OrganizationCommercialProfile.organization_id == organization_id).first()


def create_package(db: Session, organization_id: str | None, data: dict[str, Any], user_id: str | None) -> CommercialPackage:
    row = CommercialPackage(
        organization_id=organization_id,
        plan_id=data.get("plan_id"),
        segment_id=data.get("segment_id"),
        sector_id=data.get("sector_id"),
        base_package_id=data.get("base_package_id"),
        code=str(data["code"]).strip().lower(),
        name=data["name"],
        descripcion=data.get("descripcion"),
        lifecycle_status=data.get("lifecycle_status", CatalogLifecycle.BORRADOR),
        is_custom=bool(data.get("is_custom", False)),
        empleados_ia_incluidos=data.get("empleados_ia_incluidos"),
        usuarios_incluidos=data.get("usuarios_incluidos"),
        automatizaciones_incluidas=data.get("automatizaciones_incluidas"),
        consumo_ia_incluido_tokens=data.get("consumo_ia_incluido_tokens"),
        presupuesto_ia_incluido=_decimal(data.get("presupuesto_ia_incluido")),
        integraciones_incluidas=data.get("integraciones_incluidas"),
        almacenamiento_gb=data.get("almacenamiento_gb"),
        sla_nivel=data.get("sla_nivel"),
        soporte_nivel=data.get("soporte_nivel"),
        excedente_ia_por_millon=_decimal(data.get("excedente_ia_por_millon")),
        alerta_consumo_pct=_decimal(data.get("alerta_consumo_pct")),
        bloqueo_excedente=bool(data.get("bloqueo_excedente", False)),
        credential_modes_json=_json(data.get("credential_modes")) if data.get("credential_modes") else None,
        capabilities_json=_json(data.get("capabilities")) if data.get("capabilities") else None,
        servicios_incluidos_json=_json(data.get("servicios_incluidos")) if data.get("servicios_incluidos") else None,
        servicios_opcionales_json=_json(data.get("servicios_opcionales")) if data.get("servicios_opcionales") else None,
        custom_overrides_json=_json(data.get("custom_overrides")) if data.get("custom_overrides") else None,
        precio_estimado=_decimal(data.get("precio_estimado")),
    )
    db.add(row)
    db.flush()
    write_audit(db, action="segmentacion.paquete.creado", organization_id=organization_id, user_id=user_id,
                detail=_json({"package_id": row.id}), commit=False)
    return row


def list_packages(db: Session, organization_id: str, *, segment_id: str | None = None, sector_id: str | None = None) -> list[CommercialPackage]:
    q = db.query(CommercialPackage).filter(
        (CommercialPackage.organization_id == organization_id) | (CommercialPackage.organization_id.is_(None)),
        CommercialPackage.is_active.is_(True),
        CommercialPackage.lifecycle_status == CatalogLifecycle.ACTIVO,
    )
    if segment_id:
        q = q.filter((CommercialPackage.segment_id == segment_id) | (CommercialPackage.segment_id.is_(None)))
    if sector_id:
        q = q.filter((CommercialPackage.sector_id == sector_id) | (CommercialPackage.sector_id.is_(None)))
    return q.order_by(CommercialPackage.precio_estimado.nullsfirst()).all()


def get_package(db: Session, organization_id: str, package_id: str) -> CommercialPackage:
    row = (
        db.query(CommercialPackage)
        .filter(
            CommercialPackage.id == package_id,
            (CommercialPackage.organization_id == organization_id) | (CommercialPackage.organization_id.is_(None)),
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Paquete no encontrado")
    return row


def version_package(db: Session, organization_id: str, package_id: str, user_id: str | None) -> CommercialPackageVersion:
    pkg = get_package(db, organization_id, package_id)
    snap = CommercialPackageVersion(
        package_id=pkg.id,
        version_number=pkg.version_number,
        snapshot_json=_json(_package_to_dict(pkg)),
        created_by=user_id,
    )
    db.add(snap)
    pkg.version_number += 1
    db.flush()
    write_audit(db, action="segmentacion.paquete.versionado", organization_id=organization_id, user_id=user_id,
                detail=_json({"package_id": package_id, "version": snap.version_number}), commit=False)
    return snap


def version_plan(db: Session, organization_id: str, plan_id: str, user_id: str | None) -> CommercialPlanVersion:
    from app.services.commercial_service import plan_to_dict
    plan = get_plan(db, organization_id, plan_id)
    snap = CommercialPlanVersion(
        plan_id=plan.id,
        version_number=plan.version_number,
        snapshot_json=_json(plan_to_dict(plan)),
        created_by=user_id,
    )
    db.add(snap)
    plan.version_number += 1
    db.flush()
    write_audit(db, action="segmentacion.plan.versionado", organization_id=organization_id, user_id=user_id,
                detail=_json({"plan_id": plan_id, "version": snap.version_number}), commit=False)
    return snap


def _score_package_fit(profile: OrganizationCommercialProfile, pkg: CommercialPackage) -> dict[str, Any]:
    """Motor determinista de ajuste plan/paquete."""
    reasons: list[str] = []
    warnings: list[str] = []
    deficits: list[str] = []
    excesses: list[str] = []
    score = 100

    checks = [
        ("num_empleados_ia", pkg.empleados_ia_incluidos, "empleados IA"),
        ("num_usuarios", pkg.usuarios_incluidos, "usuarios"),
        ("num_integraciones", pkg.integraciones_incluidas, "integraciones"),
        ("consumo_ia_estimado", pkg.consumo_ia_incluido_tokens, "consumo IA"),
    ]
    usage_ratios: list[float] = []
    for attr, limit, label in checks:
        need = getattr(profile, attr, None)
        if need is None or limit is None:
            continue
        if need > limit:
            score -= 30
            deficits.append(f"Necesita {need} {label}, paquete incluye {limit}")
        elif need < limit * 0.4:
            score -= 10
            excesses.append(f"Solo necesita {need} {label}, paquete incluye {limit}")
            usage_ratios.append(need / limit if limit else 0)
        else:
            reasons.append(f"{label}: {need} dentro del límite {limit}")
            usage_ratios.append(need / limit if limit else 1)

    if profile.potencial_valor and pkg.precio_estimado:
        if pkg.precio_estimado > profile.potencial_valor * Decimal("0.5"):
            warnings.append("Precio estimado alto respecto al potencial de valor")
            score -= 15
        else:
            reasons.append("Precio acorde al potencial de valor")

    if profile.presupuesto_estimado and pkg.precio_estimado:
        if pkg.precio_estimado > profile.presupuesto_estimado:
            score -= 25
            deficits.append("Supera presupuesto estimado del cliente")

    if deficits:
        fit = PlanFitLevel.INSUFICIENTE
    elif excesses and (not usage_ratios or max(usage_ratios) < 0.35):
        fit = PlanFitLevel.EXCESIVO
    else:
        fit = PlanFitLevel.ADECUADO

    return {
        "package_id": pkg.id, "package_code": pkg.code, "package_name": pkg.name,
        "plan_id": pkg.plan_id, "score": max(0, score), "nivel_ajuste": fit,
        "razones": reasons, "advertencias": warnings,
        "por_que_insuficiente": deficits, "por_que_excesivo": excesses,
        "precio_estimado": float(pkg.precio_estimado) if pkg.precio_estimado else None,
    }


def recommend_plan(db: Session, organization_id: str) -> dict[str, Any]:
    profile = get_profile(db, organization_id)
    if not profile:
        raise SegmentationValidationError("No existe perfil comercial para la organización")
    packages = list_packages(db, organization_id, segment_id=profile.segment_id, sector_id=profile.sector_id)
    if not packages:
        packages = list_packages(db, organization_id)
    if not packages:
        return {
            "plan_sugerido": None, "paquete_sugerido": None,
            "nivel_ajuste": PlanFitLevel.INSUFICIENTE,
            "razones": [], "advertencias": ["No hay paquetes activos en el catálogo"],
            "alternativas": [], "plan_personalizado_recomendado": True,
        }

    scored = [_score_package_fit(profile, p) for p in packages]
    scored.sort(key=lambda x: (-x["score"], x.get("precio_estimado") or 0))
    best = scored[0]
    alternatives = scored[1:4]

    adecuados = [s for s in scored if s["nivel_ajuste"] == PlanFitLevel.ADECUADO]
    if adecuados:
        best = max(adecuados, key=lambda x: x["score"])

    plan = None
    if best.get("plan_id"):
        plan = db.query(CommercialPlan).filter(CommercialPlan.id == best["plan_id"]).first()

    write_audit(db, action="segmentacion.recomendacion.generada", organization_id=organization_id, user_id=None,
                detail=_json({"package_id": best["package_id"], "fit": best["nivel_ajuste"]}), commit=False)

    return {
        "plan_sugerido": {"id": plan.id, "code": plan.code, "name": plan.name} if plan else None,
        "paquete_sugerido": {"id": best["package_id"], "code": best["package_code"], "name": best["package_name"]},
        "nivel_ajuste": best["nivel_ajuste"],
        "razones": best["razones"],
        "advertencias": best["advertencias"],
        "por_que_insuficiente": best.get("por_que_insuficiente", []),
        "por_que_excesivo": best.get("por_que_excesivo", []),
        "alternativas": alternatives,
        "plan_personalizado_recomendado": best["nivel_ajuste"] == PlanFitLevel.INSUFICIENTE,
        "perfil": _profile_to_dict(profile),
    }


def compare_packages(db: Session, organization_id: str, package_ids: list[str]) -> dict[str, Any]:
    items = []
    for pid in package_ids:
        pkg = get_package(db, organization_id, pid)
        items.append(_package_to_dict(pkg))
    if len(items) < 2:
        raise SegmentationValidationError("Se requieren al menos 2 paquetes para comparar")
    keys = [
        "empleados_ia_incluidos", "usuarios_incluidos", "automatizaciones_incluidas",
        "consumo_ia_incluido_tokens", "integraciones_incluidas", "almacenamiento_gb",
        "sla_nivel", "soporte_nivel", "precio_estimado",
    ]
    diferencias: dict[str, list[Any]] = {}
    for k in keys:
        vals = [i.get(k) for i in items]
        if len(set(str(v) for v in vals)) > 1:
            diferencias[k] = vals
    return {"paquetes": items, "diferencias": diferencias}


def suggest_scaling(db: Session, organization_id: str, changes: dict[str, Any]) -> dict[str, Any]:
    profile = get_profile(db, organization_id)
    if not profile:
        raise SegmentationValidationError("Perfil comercial requerido")
    current = recommend_plan(db, organization_id)
    simulated = OrganizationCommercialProfile(
        organization_id=organization_id,
        num_usuarios=changes.get("num_usuarios", profile.num_usuarios),
        num_empleados_ia=changes.get("num_empleados_ia", profile.num_empleados_ia),
        num_integraciones=changes.get("num_integraciones", profile.num_integraciones),
        consumo_ia_estimado=changes.get("consumo_ia_estimado", profile.consumo_ia_estimado),
        potencial_valor=profile.potencial_valor,
        presupuesto_estimado=profile.presupuesto_estimado,
        segment_id=profile.segment_id,
        sector_id=profile.sector_id,
    )
    packages = list_packages(db, organization_id)
    scored = [_score_package_fit(simulated, p) for p in packages]
    scored.sort(key=lambda x: -x["score"])
    new_best = scored[0] if scored else None
    direction = ScaleDirection.MANTENER
    if new_best and current.get("paquete_sugerido"):
        old_price = next((p.precio_estimado for p in packages if p.id == current["paquete_sugerido"]["id"]), None)
        new_pkg = next((p for p in packages if p.id == new_best["package_id"]), None)
        if new_pkg and old_price and new_pkg.precio_estimado:
            if new_pkg.precio_estimado > old_price * Decimal("1.1"):
                direction = ScaleDirection.SUBIR
            elif new_pkg.precio_estimado < old_price * Decimal("0.9"):
                direction = ScaleDirection.BAJAR
    return {
        "direccion": direction,
        "paquete_actual": current.get("paquete_sugerido"),
        "paquete_sugerido_tras_cambio": new_best,
        "cambios_aplicados": changes,
    }


def apply_discount(
    db: Session,
    organization_id: str,
    data: dict[str, Any],
    user_id: str,
) -> dict[str, Any]:
    valor_original = _decimal(data.get("valor_original"))
    if valor_original is None or valor_original <= 0:
        raise SegmentationValidationError("valor_original inválido")
    tipo = data.get("tipo", DiscountType.PORCENTAJE)
    if tipo not in DiscountType.ALL:
        raise SegmentationValidationError("Tipo de descuento no válido")
    desc = _decimal(data.get("valor_descuento")) or Decimal("0")
    if tipo == DiscountType.PORCENTAJE:
        valor_final = (valor_original * (Decimal("1") - desc / Decimal("100"))).quantize(Decimal("0.0001"))
    else:
        valor_final = (valor_original - desc).quantize(Decimal("0.0001"))
    piso = _decimal(data.get("piso_economico"))
    advertencias: list[str] = []
    bloqueado = False
    if piso and valor_final < piso:
        advertencias.append("El descuento deja el precio por debajo del piso económico de 1280")
        if data.get("bloquear_bajo_piso", True):
            bloqueado = True
    row = CommercialDiscount(
        organization_id=organization_id,
        target_type=data.get("target_type", "paquete"),
        target_id=data["target_id"],
        tipo=tipo,
        valor_descuento=desc,
        valor_original=valor_original,
        valor_final=valor_final,
        motivo=data.get("motivo"),
        user_id=user_id,
    )
    if not bloqueado:
        db.add(row)
    db.flush()
    write_audit(db, action="segmentacion.descuento.aplicado", organization_id=organization_id, user_id=user_id,
                detail=_json({"target_id": data["target_id"], "valor_final": float(valor_final), "bloqueado": bloqueado}),
                commit=False)
    return {
        "valor_original": float(valor_original),
        "valor_descuento": float(desc),
        "valor_final": float(valor_final),
        "tipo": tipo,
        "advertencias": advertencias,
        "bloqueado": bloqueado,
        "discount_id": row.id if not bloqueado else None,
    }


def create_custom_package(
    db: Session,
    organization_id: str,
    base_package_id: str,
    overrides: dict[str, Any],
    user_id: str | None,
) -> CommercialPackage:
    base = get_package(db, organization_id, base_package_id)
    data = _package_to_dict(base)
    data.update(overrides)
    data["code"] = overrides.get("code", f"{base.code}-custom-{organization_id[:8]}")
    data["name"] = overrides.get("name", f"{base.name} (personalizado)")
    data["base_package_id"] = base_package_id
    data["is_custom"] = True
    data["custom_overrides"] = overrides
    return create_package(db, organization_id, data, user_id)


def price_with_package(
    db: Session,
    organization_id: str,
    package_id: str,
    valor_atribuible: float,
    costo_total: float | None = None,
) -> dict[str, Any]:
    """Reutiliza motor 1280 alimentado por paquete/plan."""
    pkg = get_package(db, organization_id, package_id)
    plan = get_plan(db, organization_id, pkg.plan_id) if pkg.plan_id else None
    costo = _decimal(costo_total) or pkg.precio_estimado or Decimal("0")
    fraccion = plan.fraccion_valor_sugerida if plan and plan.fraccion_valor_sugerida else Decimal("0.25")
    margen = plan.margen_minimo_pct if plan else Decimal("0.15")
    precio_base = plan.precio_base_mensual if plan and plan.precio_base_mensual else Decimal("0")
    return _compute_economics(
        valor_atribuible=_decimal(valor_atribuible) or Decimal("0"),
        costo_total=costo,
        fraccion=fraccion,
        margen_min=margen,
        precio_base=precio_base,
        precio_minimo=plan.precio_minimo if plan else None,
        precio_maximo=plan.precio_maximo if plan else None,
    )


def build_proposal_catalog_snapshot(
    db: Session,
    organization_id: str,
    *,
    plan_id: str | None,
    package_id: str | None,
    segment_id: str | None,
) -> dict[str, Any]:
    snap: dict[str, Any] = {}
    if plan_id:
        from app.services.commercial_service import plan_to_dict
        plan = get_plan(db, organization_id, plan_id)
        snap["plan"] = plan_to_dict(plan)
        snap["plan_version"] = plan.version_number
    if package_id:
        pkg = get_package(db, organization_id, package_id)
        snap["package"] = _package_to_dict(pkg)
        snap["package_version"] = pkg.version_number
    if segment_id:
        seg = db.query(CommercialSegment).filter(CommercialSegment.id == segment_id).first()
        if seg:
            snap["segment"] = _segment_to_dict(seg)
    profile = get_profile(db, organization_id)
    if profile:
        snap["profile"] = _profile_to_dict(profile)
    return snap


def seed_default_capabilities(db: Session) -> None:
    from app.segmentation_enums import CapabilityCode
    for code in CapabilityCode.ALL:
        if db.query(CommercialCapability).filter(CommercialCapability.code == code).first():
            continue
        db.add(CommercialCapability(code=code, name=code.replace("_", " ").title()))


def seed_default_sectors(db: Session) -> None:
    defaults = [
        ("salud", "Salud"), ("software", "Software / Tecnología"),
        ("servicios_profesionales", "Servicios profesionales"), ("logistica", "Logística"),
        ("transporte", "Transporte"), ("comercio", "Comercio"), ("industria", "Industria"),
        ("educacion", "Educación"), ("finanzas", "Finanzas"), ("otros", "Otros"),
    ]
    for code, name in defaults:
        if db.query(CommercialSector).filter(CommercialSector.code == code, CommercialSector.organization_id.is_(None)).first():
            continue
        db.add(CommercialSector(organization_id=None, code=code, name=name, lifecycle_status=CatalogLifecycle.ACTIVO))
