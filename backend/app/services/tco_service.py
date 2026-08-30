"""Servicio — TCO y ecosistema de aliados (1320)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.commercial_models import CommercialProposal
from app.orchestration_models import FinOpsRecord
from app.tco_enums import (
    CategoriaCostoDefault,
    MetodoDistribucion,
    NaturalezaCosto,
    Periodicidad,
    RiesgoProveedor,
    TipoCosto,
    TipoProveedorAliado,
    TipoSimulacion,
)
from app.tco_models import (
    TcoAlertaEconomica,
    TcoAlianza,
    TcoAuditoria,
    TcoCategoriaCosto,
    TcoContratoCondicion,
    TcoCosto,
    TcoCostoHistorico,
    TcoDistribucion,
    TcoProveedorAliado,
    TcoSimulacion,
    TcoSnapshot,
    TcoTarifa,
    TcoTarifaTramo,
)


class TcoValidationError(ValueError):
    pass


CONCENTRACION_UMBRAL = Decimal("0.40")
_RIESGO_SCORE = {"BAJO": 1, "MEDIO": 2, "ALTO": 3}


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


def _decimal(value: float | Decimal | str | None, default: Decimal | None = None) -> Decimal | None:
    if value is None:
        return default
    return Decimal(str(value))


def _audit(db: Session, org_id: str, accion: str, entidad: str, entidad_id: str | None, user_id: str | None, detalle: Any = None) -> None:
    db.add(
        TcoAuditoria(
            organization_id=org_id,
            accion=accion,
            entidad=entidad,
            entidad_id=entidad_id,
            detalle_json=_json(detalle) if detalle is not None else None,
            user_id=user_id,
        )
    )


def _ensure_org_scope(db: Session, org_id: str, entity_org_id: str) -> None:
    if entity_org_id != org_id:
        raise HTTPException(status_code=404, detail="Recurso no encontrado")


# --- Catálogo categorías ---

def bootstrap_categorias_default(db: Session, org_id: str) -> list[TcoCategoriaCosto]:
    existing = db.query(TcoCategoriaCosto).filter(
        TcoCategoriaCosto.organization_id == org_id,
    ).count()
    if existing:
        return list_categorias(db, org_id)
    rows = []
    for code in sorted(CategoriaCostoDefault.ALL):
        row = TcoCategoriaCosto(
            organization_id=org_id,
            code=code,
            nombre=code.replace("_", " ").title(),
            es_global=False,
        )
        db.add(row)
        rows.append(row)
    db.flush()
    return rows


def list_categorias(db: Session, org_id: str) -> list[TcoCategoriaCosto]:
    return (
        db.query(TcoCategoriaCosto)
        .filter(
            (TcoCategoriaCosto.organization_id == org_id) | (TcoCategoriaCosto.es_global.is_(True)),
            TcoCategoriaCosto.is_active.is_(True),
        )
        .order_by(TcoCategoriaCosto.code)
        .all()
    )


def categoria_to_dict(row: TcoCategoriaCosto) -> dict[str, Any]:
    return {
        "id": row.id,
        "code": row.code,
        "nombre": row.nombre,
        "descripcion": row.descripcion,
        "es_global": row.es_global,
    }


def create_categoria(db: Session, org_id: str, data: dict[str, Any], user_id: str | None) -> TcoCategoriaCosto:
    row = TcoCategoriaCosto(
        organization_id=org_id if not data.get("es_global") else None,
        code=data["code"].upper(),
        nombre=data["nombre"],
        descripcion=data.get("descripcion"),
        es_global=bool(data.get("es_global")),
    )
    db.add(row)
    db.flush()
    _audit(db, org_id, "CREAR", "categoria", row.id, user_id, {"code": row.code})
    return row


def _resolve_categoria(db: Session, org_id: str, categoria_id: str | None, categoria_code: str | None) -> TcoCategoriaCosto | None:
    if categoria_id:
        row = db.query(TcoCategoriaCosto).filter(TcoCategoriaCosto.id == categoria_id).first()
        if not row:
            raise TcoValidationError("Categoría no encontrada")
        if row.organization_id and row.organization_id != org_id and not row.es_global:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
        return row
    if categoria_code:
        row = (
            db.query(TcoCategoriaCosto)
            .filter(
                TcoCategoriaCosto.code == categoria_code.upper(),
                (TcoCategoriaCosto.organization_id == org_id) | (TcoCategoriaCosto.es_global.is_(True)),
            )
            .first()
        )
        if not row:
            raise TcoValidationError(f"Categoría {categoria_code} no encontrada")
        return row
    return None


# --- Proveedores ---

def _next_proveedor_codigo(db: Session, org_id: str) -> str:
    count = db.query(func.count(TcoProveedorAliado.id)).filter(TcoProveedorAliado.organization_id == org_id).scalar() or 0
    return f"PROV-{count + 1:04d}"


def list_proveedores(db: Session, org_id: str) -> list[TcoProveedorAliado]:
    return (
        db.query(TcoProveedorAliado)
        .filter(TcoProveedorAliado.organization_id == org_id)
        .order_by(TcoProveedorAliado.nombre)
        .all()
    )


def get_proveedor(db: Session, org_id: str, proveedor_id: str) -> TcoProveedorAliado:
    row = db.query(TcoProveedorAliado).filter(TcoProveedorAliado.id == proveedor_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    _ensure_org_scope(db, org_id, row.organization_id)
    return row


def proveedor_to_dict(row: TcoProveedorAliado) -> dict[str, Any]:
    return {
        "id": row.id,
        "codigo": row.codigo,
        "nombre": row.nombre,
        "tipo": row.tipo,
        "contacto": row.contacto,
        "descripcion": row.descripcion,
        "riesgo_nivel": row.riesgo_nivel,
        "riesgo_criterio": row.riesgo_criterio,
        "riesgo_justificacion": row.riesgo_justificacion,
        "riesgo_fecha": row.riesgo_fecha.isoformat() if row.riesgo_fecha else None,
        "estado": row.estado,
    }


def create_proveedor(db: Session, org_id: str, data: dict[str, Any], user_id: str | None) -> TcoProveedorAliado:
    tipo = data.get("tipo", TipoProveedorAliado.OTRO)
    if tipo not in TipoProveedorAliado.ALL:
        raise TcoValidationError(f"Tipo de proveedor inválido: {tipo}")
    riesgo = data.get("riesgo_nivel", RiesgoProveedor.MEDIO)
    if riesgo not in RiesgoProveedor.ALL:
        raise TcoValidationError(f"Nivel de riesgo inválido: {riesgo}")
    row = TcoProveedorAliado(
        organization_id=org_id,
        codigo=data.get("codigo") or _next_proveedor_codigo(db, org_id),
        nombre=data["nombre"],
        tipo=tipo,
        contacto=data.get("contacto"),
        descripcion=data.get("descripcion"),
        riesgo_nivel=riesgo,
        riesgo_criterio=data.get("riesgo_criterio"),
        riesgo_justificacion=data.get("riesgo_justificacion"),
        riesgo_fecha=_utcnow() if data.get("riesgo_justificacion") else None,
        riesgo_responsable_id=user_id,
    )
    db.add(row)
    db.flush()
    _audit(db, org_id, "CREAR", "proveedor", row.id, user_id, proveedor_to_dict(row))
    return row


def update_riesgo_proveedor(db: Session, org_id: str, proveedor_id: str, data: dict[str, Any], user_id: str | None) -> TcoProveedorAliado:
    row = get_proveedor(db, org_id, proveedor_id)
    nivel = data["riesgo_nivel"]
    if nivel not in RiesgoProveedor.ALL:
        raise TcoValidationError(f"Nivel de riesgo inválido: {nivel}")
    row.riesgo_nivel = nivel
    row.riesgo_criterio = data.get("riesgo_criterio")
    row.riesgo_justificacion = data.get("riesgo_justificacion")
    row.riesgo_fecha = _utcnow()
    row.riesgo_responsable_id = user_id
    db.flush()
    _audit(db, org_id, "CAMBIO_RIESGO", "proveedor", row.id, user_id, {"riesgo_nivel": nivel})
    return row


# --- Contratos ---

def create_contrato(db: Session, org_id: str, data: dict[str, Any], user_id: str | None) -> TcoContratoCondicion:
    get_proveedor(db, org_id, data["proveedor_id"])
    row = TcoContratoCondicion(
        organization_id=org_id,
        proveedor_id=data["proveedor_id"],
        moneda=data.get("moneda", "COP"),
        tipo_tarifa=data.get("tipo_tarifa"),
        minimo=_decimal(data.get("minimo")),
        maximo=_decimal(data.get("maximo")),
        compromiso=data.get("compromiso"),
        descuento_pct=_decimal(data.get("descuento_pct")),
        condiciones=data.get("condiciones"),
        sla=data.get("sla"),
        fecha_inicio=data.get("fecha_inicio"),
        fecha_fin=data.get("fecha_fin"),
    )
    db.add(row)
    db.flush()
    _audit(db, org_id, "CREAR", "contrato", row.id, user_id, {"proveedor_id": row.proveedor_id})
    return row


def contrato_to_dict(row: TcoContratoCondicion) -> dict[str, Any]:
    return {
        "id": row.id,
        "proveedor_id": row.proveedor_id,
        "moneda": row.moneda,
        "tipo_tarifa": row.tipo_tarifa,
        "minimo": float(row.minimo) if row.minimo is not None else None,
        "maximo": float(row.maximo) if row.maximo is not None else None,
        "sla": row.sla,
        "fecha_inicio": row.fecha_inicio.isoformat() if row.fecha_inicio else None,
        "fecha_fin": row.fecha_fin.isoformat() if row.fecha_fin else None,
        "estado": row.estado,
    }


def list_contratos(db: Session, org_id: str, proveedor_id: str | None = None) -> list[TcoContratoCondicion]:
    q = db.query(TcoContratoCondicion).filter(TcoContratoCondicion.organization_id == org_id)
    if proveedor_id:
        q = q.filter(TcoContratoCondicion.proveedor_id == proveedor_id)
    return q.order_by(TcoContratoCondicion.created_at.desc()).all()


# --- Tarifas ---

def calcular_tarifa_volumen(tramos: list[dict[str, Any]], unidades: Decimal) -> dict[str, Any]:
    """Cálculo determinista por tramos — ejemplo 0-1M → A, 1-5M → B, >5M → C."""
    if not tramos:
        return {"costo": Decimal("0"), "tramo_aplicado": None, "explicacion": "Sin tramos definidos"}
    ordenados = sorted(tramos, key=lambda t: t.get("orden", 0))
    restante = unidades
    costo_total = Decimal("0")
    tramo_aplicado = None
    for tramo in ordenados:
        desde = _decimal(tramo.get("desde_unidades"), Decimal("0")) or Decimal("0")
        hasta = _decimal(tramo.get("hasta_unidades"))
        precio = _decimal(tramo.get("precio_unidad"), Decimal("0")) or Decimal("0")
        if unidades < desde:
            continue
        if hasta is None:
            unidades_tramo = restante
        else:
            cap = hasta - desde
            unidades_tramo = min(restante, cap)
        if unidades_tramo <= 0:
            continue
        costo_total += unidades_tramo * precio
        restante -= unidades_tramo
        tramo_aplicado = tramo
        if restante <= 0:
            break
    return {
        "costo": costo_total,
        "tramo_aplicado": tramo_aplicado,
        "explicacion": f"Costo por {unidades} unidades en {len(ordenados)} tramo(s)",
    }


def create_tarifa(db: Session, org_id: str, data: dict[str, Any], user_id: str | None) -> TcoTarifa:
    get_proveedor(db, org_id, data["proveedor_id"])
    row = TcoTarifa(
        organization_id=org_id,
        proveedor_id=data["proveedor_id"],
        nombre=data["nombre"],
        unidad=data.get("unidad", "unidad"),
        moneda=data.get("moneda", "COP"),
        tipo=data.get("tipo", "UNIDAD"),
        monto_base=_decimal(data.get("monto_base")),
        periodicidad=data.get("periodicidad"),
        vigente_desde=data.get("vigente_desde"),
        vigente_hasta=data.get("vigente_hasta"),
    )
    db.add(row)
    db.flush()
    for i, tramo in enumerate(data.get("tramos") or []):
        db.add(
            TcoTarifaTramo(
                tarifa_id=row.id,
                desde_unidades=_decimal(tramo.get("desde_unidades"), Decimal("0")) or Decimal("0"),
                hasta_unidades=_decimal(tramo.get("hasta_unidades")),
                precio_unidad=_decimal(tramo["precio_unidad"], Decimal("0")) or Decimal("0"),
                orden=tramo.get("orden", i),
            )
        )
    db.flush()
    _audit(db, org_id, "CREAR", "tarifa", row.id, user_id, {"nombre": row.nombre})
    return row


def tarifa_to_dict(db: Session, row: TcoTarifa) -> dict[str, Any]:
    tramos = (
        db.query(TcoTarifaTramo)
        .filter(TcoTarifaTramo.tarifa_id == row.id)
        .order_by(TcoTarifaTramo.orden)
        .all()
    )
    return {
        "id": row.id,
        "proveedor_id": row.proveedor_id,
        "nombre": row.nombre,
        "unidad": row.unidad,
        "moneda": row.moneda,
        "tipo": row.tipo,
        "monto_base": float(row.monto_base) if row.monto_base is not None else None,
        "periodicidad": row.periodicidad,
        "vigente_desde": row.vigente_desde.isoformat() if row.vigente_desde else None,
        "vigente_hasta": row.vigente_hasta.isoformat() if row.vigente_hasta else None,
        "estado": row.estado,
        "tramos": [
            {
                "desde_unidades": float(t.desde_unidades),
                "hasta_unidades": float(t.hasta_unidades) if t.hasta_unidades is not None else None,
                "precio_unidad": float(t.precio_unidad),
                "orden": t.orden,
            }
            for t in tramos
        ],
    }


def list_tarifas(db: Session, org_id: str, proveedor_id: str | None = None) -> list[dict[str, Any]]:
    q = db.query(TcoTarifa).filter(TcoTarifa.organization_id == org_id)
    if proveedor_id:
        q = q.filter(TcoTarifa.proveedor_id == proveedor_id)
    return [tarifa_to_dict(db, r) for r in q.order_by(TcoTarifa.nombre).all()]


# --- Costos ---

def _aplicar_conversion(monto: Decimal, moneda: str, tasa: Decimal | None, destino: str | None) -> tuple[Decimal | None, str | None]:
    if not destino or moneda == destino or tasa is None:
        return None, None
    return monto * tasa, destino


def create_costo(db: Session, org_id: str, data: dict[str, Any], user_id: str | None) -> TcoCosto:
    bootstrap_categorias_default(db, org_id)
    cat = _resolve_categoria(db, org_id, data.get("categoria_id"), data.get("categoria_code"))
    if data.get("proveedor_id"):
        get_proveedor(db, org_id, data["proveedor_id"])
    tipo = data.get("tipo_costo", TipoCosto.FIJO)
    if tipo not in TipoCosto.ALL:
        raise TcoValidationError(f"Tipo de costo inválido: {tipo}")
    naturaleza = data.get("naturaleza", NaturalezaCosto.ESTIMADO)
    if naturaleza not in NaturalezaCosto.ALL:
        raise TcoValidationError(f"Naturaleza inválida: {naturaleza}")
    periodicidad = data.get("periodicidad", Periodicidad.MENSUAL)
    monto = _decimal(data["monto"], Decimal("0")) or Decimal("0")
    moneda = data.get("moneda", "COP")
    tasa = _decimal(data.get("tasa_conversion"))
    destino = data.get("moneda_destino")
    monto_conv, _ = _aplicar_conversion(monto, moneda, tasa, destino)
    row = TcoCosto(
        organization_id=org_id,
        categoria_id=cat.id if cat else None,
        proveedor_id=data.get("proveedor_id"),
        nombre=data["nombre"],
        tipo_costo=tipo,
        naturaleza=naturaleza,
        periodicidad=periodicidad,
        unidad=data.get("unidad"),
        cantidad=_decimal(data.get("cantidad")),
        monto=monto,
        moneda=moneda,
        tasa_conversion=tasa,
        tasa_fecha=data.get("tasa_fecha") or (_utcnow() if tasa else None),
        monto_convertido=monto_conv,
        moneda_destino=destino,
        proposal_id=data.get("proposal_id"),
        finops_record_id=data.get("finops_record_id"),
        employee_id=data.get("employee_id"),
        integracion_ref=data.get("integracion_ref"),
        periodo_ref=data.get("periodo_ref"),
        notas=data.get("notas"),
        created_by=user_id,
    )
    db.add(row)
    db.flush()
    _audit(db, org_id, "CREAR", "costo", row.id, user_id, {"nombre": row.nombre, "monto": float(monto)})
    return row


def costo_to_dict(row: TcoCosto, categoria_code: str | None = None) -> dict[str, Any]:
    return {
        "id": row.id,
        "categoria_id": row.categoria_id,
        "categoria_code": categoria_code,
        "proveedor_id": row.proveedor_id,
        "nombre": row.nombre,
        "tipo_costo": row.tipo_costo,
        "naturaleza": row.naturaleza,
        "periodicidad": row.periodicidad,
        "unidad": row.unidad,
        "cantidad": float(row.cantidad) if row.cantidad is not None else None,
        "monto": float(row.monto),
        "moneda": row.moneda,
        "tasa_conversion": float(row.tasa_conversion) if row.tasa_conversion is not None else None,
        "monto_convertido": float(row.monto_convertido) if row.monto_convertido is not None else None,
        "moneda_destino": row.moneda_destino,
        "proposal_id": row.proposal_id,
        "finops_record_id": row.finops_record_id,
        "employee_id": row.employee_id,
        "periodo_ref": row.periodo_ref,
        "version": row.version,
        "is_active": row.is_active,
    }


def list_costos(db: Session, org_id: str, naturaleza: str | None = None) -> list[dict[str, Any]]:
    q = db.query(TcoCosto).filter(TcoCosto.organization_id == org_id, TcoCosto.is_active.is_(True))
    if naturaleza:
        q = q.filter(TcoCosto.naturaleza == naturaleza)
    rows = q.order_by(TcoCosto.nombre).all()
    cats = {c.id: c.code for c in list_categorias(db, org_id)}
    return [costo_to_dict(r, cats.get(r.categoria_id)) for r in rows]


def update_costo(db: Session, org_id: str, costo_id: str, data: dict[str, Any], user_id: str | None) -> TcoCosto:
    row = db.query(TcoCosto).filter(TcoCosto.id == costo_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Costo no encontrado")
    _ensure_org_scope(db, org_id, row.organization_id)
    snapshot = costo_to_dict(row)
    db.add(
        TcoCostoHistorico(
            costo_id=row.id,
            organization_id=org_id,
            snapshot_json=_json(snapshot),
            motivo=data.get("motivo", "Actualización"),
            created_by=user_id,
        )
    )
    if data.get("nombre"):
        row.nombre = data["nombre"]
    if data.get("monto") is not None:
        row.monto = _decimal(data["monto"], row.monto) or row.monto
    if data.get("naturaleza"):
        row.naturaleza = data["naturaleza"]
    if data.get("cantidad") is not None:
        row.cantidad = _decimal(data["cantidad"])
    if data.get("notas") is not None:
        row.notas = data["notas"]
    row.version += 1
    row.updated_at = _utcnow()
    db.flush()
    _audit(db, org_id, "CAMBIO_COSTO", "costo", row.id, user_id, {"version": row.version, "motivo": data.get("motivo")})
    return row


# --- Distribución ---

def create_distribucion(db: Session, org_id: str, data: dict[str, Any], user_id: str | None) -> TcoDistribucion:
    costo = db.query(TcoCosto).filter(TcoCosto.id == data["costo_id"]).first()
    if not costo:
        raise HTTPException(status_code=404, detail="Costo no encontrado")
    _ensure_org_scope(db, org_id, costo.organization_id)
    metodo = data["metodo"]
    if metodo not in MetodoDistribucion.ALL:
        raise TcoValidationError(f"Método de distribución inválido: {metodo}")
    asignaciones = data.get("asignaciones") or []
    total_pct = sum(_decimal(a.get("porcentaje"), Decimal("0")) or Decimal("0") for a in asignaciones if "porcentaje" in a)
    if metodo == MetodoDistribucion.PORCENTAJE_FIJO and total_pct and abs(total_pct - Decimal("100")) > Decimal("0.01"):
        raise TcoValidationError(f"Los porcentajes deben sumar 100% (actual: {total_pct})")
    row = TcoDistribucion(
        organization_id=org_id,
        costo_id=costo.id,
        metodo=metodo,
        criterio_json=_json(data.get("criterio")),
        asignaciones_json=_json(asignaciones),
        created_by=user_id,
    )
    db.add(row)
    db.flush()
    _audit(db, org_id, "DISTRIBUCION", "costo", costo.id, user_id, {"metodo": metodo, "asignaciones": asignaciones})
    return row


def distribucion_to_dict(row: TcoDistribucion) -> dict[str, Any]:
    return {
        "id": row.id,
        "costo_id": row.costo_id,
        "metodo": row.metodo,
        "criterio": _parse_json(row.criterio_json),
        "asignaciones": _parse_json(row.asignaciones_json),
        "created_at": row.created_at.isoformat(),
    }


# --- FinOps integración ---

def _finops_costo_ia(db: Session, org_id: str) -> Decimal:
    total = (
        db.query(func.coalesce(func.sum(FinOpsRecord.cost), 0))
        .filter(FinOpsRecord.organization_id == org_id)
        .scalar()
    )
    return _decimal(total, Decimal("0")) or Decimal("0")


def _finops_por_proveedor(db: Session, org_id: str) -> dict[str, Decimal]:
    rows = (
        db.query(FinOpsRecord.provider, func.coalesce(func.sum(FinOpsRecord.cost), 0))
        .filter(FinOpsRecord.organization_id == org_id, FinOpsRecord.provider.isnot(None))
        .group_by(FinOpsRecord.provider)
        .all()
    )
    return {str(p): _decimal(c, Decimal("0")) or Decimal("0") for p, c in rows}


# --- TCO cálculo ---

def _normalizar_mensual(monto: Decimal, periodicidad: str) -> Decimal:
    if periodicidad == Periodicidad.MENSUAL:
        return monto
    if periodicidad == Periodicidad.TRIMESTRAL:
        return monto / Decimal("3")
    if periodicidad == Periodicidad.ANUAL:
        return monto / Decimal("12")
    return monto


def calcular_tco(db: Session, org_id: str, params: dict[str, Any], user_id: str | None) -> dict[str, Any]:
    bootstrap_categorias_default(db, org_id)
    tipo = params.get("tipo", NaturalezaCosto.ESTIMADO)
    moneda_dest = params.get("moneda_destino", "COP")
    tasa_global = _decimal(params.get("tasa_conversion"))
    incluir_finops = params.get("incluir_finops", True)

    costos = (
        db.query(TcoCosto)
        .filter(TcoCosto.organization_id == org_id, TcoCosto.is_active.is_(True), TcoCosto.naturaleza == tipo)
        .all()
    )
    cats = {c.id: c for c in list_categorias(db, org_id)}
    desglose: dict[str, Decimal] = {}
    por_proveedor: dict[str, Decimal] = {}
    items: list[dict[str, Any]] = []
    total = Decimal("0")

    for c in costos:
        monto = c.monto_convertido if c.monto_convertido is not None else c.monto
        if c.moneda != moneda_dest and c.monto_convertido is None and tasa_global:
            monto = c.monto * tasa_global
        monto_mensual = _normalizar_mensual(monto, c.periodicidad)
        cat_code = cats[c.categoria_id].code if c.categoria_id and c.categoria_id in cats else "OTROS"
        desglose[cat_code] = desglose.get(cat_code, Decimal("0")) + monto_mensual
        total += monto_mensual
        if c.proveedor_id:
            por_proveedor[c.proveedor_id] = por_proveedor.get(c.proveedor_id, Decimal("0")) + monto_mensual
        items.append({"id": c.id, "nombre": c.nombre, "categoria": cat_code, "monto_mensual": float(monto_mensual)})

    finops_ia = Decimal("0")
    finops_total = Decimal("0")
    finops_proveedores: dict[str, float] = {}
    if incluir_finops:
        finops_ia = _finops_costo_ia(db, org_id)
        finops_total = finops_ia
        finops_proveedores = {k: float(v) for k, v in _finops_por_proveedor(db, org_id).items()}
        desglose["IA"] = desglose.get("IA", Decimal("0")) + finops_ia
        total += finops_ia

    ingreso = _decimal(params.get("ingreso"))
    if ingreso is None and params.get("proposal_id"):
        prop = db.query(CommercialProposal).filter(
            CommercialProposal.id == params["proposal_id"],
            CommercialProposal.organization_id == org_id,
        ).first()
        if prop:
            ingreso = prop.precio_final or prop.precio_sugerido

    margen_bruto = None
    margen_pct = None
    punto_equilibrio = None
    if ingreso is not None:
        margen_bruto = ingreso - total
        margen_pct = (margen_bruto / ingreso * Decimal("100")) if ingreso > 0 else Decimal("0")
        punto_equilibrio = total

    concentracion = _calcular_concentracion(por_proveedor, finops_proveedores, total)
    alertas = _generar_alertas(
        db, org_id, total, margen_pct, params.get("margen_minimo_pct"),
        concentracion, tipo,
    )

    proveedores_detalle = []
    for pid, monto in por_proveedor.items():
        prov = db.query(TcoProveedorAliado).filter(TcoProveedorAliado.id == pid).first()
        if prov:
            proveedores_detalle.append({
                "id": pid,
                "nombre": prov.nombre,
                "monto": float(monto),
                "pct": float(monto / total * 100) if total > 0 else 0,
            })

    resultado = {
        "organization_id": org_id,
        "periodo": params.get("periodo"),
        "escenario": params.get("escenario"),
        "tipo": tipo,
        "moneda": moneda_dest,
        "total": float(total),
        "desglose": {k: float(v) for k, v in desglose.items()},
        "items": items,
        "finops_ia": float(finops_ia),
        "finops_total": float(finops_total),
        "finops_proveedores": finops_proveedores,
        "ingreso": float(ingreso) if ingreso is not None else None,
        "margen_bruto": float(margen_bruto) if margen_bruto is not None else None,
        "margen_pct": float(margen_pct) if margen_pct is not None else None,
        "punto_equilibrio": float(punto_equilibrio) if punto_equilibrio is not None else None,
        "proveedores": proveedores_detalle,
        "concentracion": concentracion,
        "alertas": alertas,
        "explicacion": _explicar_tco(desglose, total, margen_pct),
    }

    if params.get("guardar_snapshot"):
        snap = TcoSnapshot(
            organization_id=org_id,
            periodo=params.get("periodo"),
            escenario=params.get("escenario"),
            tipo=tipo,
            total=total,
            desglose_json=_json(resultado["desglose"]),
            ingreso=ingreso,
            margen_bruto=margen_bruto,
            margen_pct=margen_pct,
            punto_equilibrio=punto_equilibrio,
            finops_ia=finops_ia,
            finops_total=finops_total,
            proveedores_json=_json(proveedores_detalle),
            concentracion_json=_json(concentracion),
            alertas_json=_json(alertas),
            proposal_id=params.get("proposal_id"),
            es_simulacion=False,
            explicacion=resultado["explicacion"],
            created_by=user_id,
        )
        db.add(snap)
        db.flush()
        resultado["snapshot_id"] = snap.id

    return resultado


def _explicar_tco(desglose: dict[str, Decimal], total: Decimal, margen_pct: Decimal | None) -> str:
    partes = [f"TCO total mensual: {float(total):,.2f}"]
    top = sorted(desglose.items(), key=lambda x: x[1], reverse=True)[:3]
    if top:
        partes.append("Principales categorías: " + ", ".join(f"{k} ({float(v):,.2f})" for k, v in top))
    if margen_pct is not None:
        partes.append(f"Margen bruto: {float(margen_pct):.1f}%")
    return ". ".join(partes)


def _calcular_concentracion(
    por_proveedor: dict[str, Decimal],
    finops_proveedores: dict[str, float],
    total: Decimal,
) -> dict[str, Any]:
    if total <= 0:
        return {"max_proveedor_pct": 0, "max_ia_proveedor_pct": 0, "advertencia": False}
    max_prov = Decimal("0")
    for m in por_proveedor.values():
        pct = m / total
        if pct > max_prov:
            max_prov = pct
    max_ia = Decimal("0")
    finops_sum = sum(Decimal(str(v)) for v in finops_proveedores.values())
    if finops_sum > 0:
        for v in finops_proveedores.values():
            pct = Decimal(str(v)) / finops_sum
            if pct > max_ia:
                max_ia = pct
    return {
        "max_proveedor_pct": float(max_prov * 100),
        "max_ia_proveedor_pct": float(max_ia * 100),
        "advertencia": max_prov >= CONCENTRACION_UMBRAL or max_ia >= CONCENTRACION_UMBRAL,
        "umbral_pct": float(CONCENTRACION_UMBRAL * 100),
    }


def _generar_alertas(
    db: Session,
    org_id: str,
    total: Decimal,
    margen_pct: Decimal | None,
    margen_minimo: float | None,
    concentracion: dict[str, Any],
    tipo: str,
) -> list[dict[str, Any]]:
    alertas: list[dict[str, Any]] = []
    minimo = _decimal(margen_minimo, Decimal("15")) or Decimal("15")
    if margen_pct is not None and margen_pct < minimo:
        alertas.append({
            "tipo": "MARGEN_BAJO",
            "mensaje": f"Margen {float(margen_pct):.1f}% inferior al mínimo {float(minimo)}%",
            "severidad": "ALTA",
        })
    if concentracion.get("advertencia"):
        alertas.append({
            "tipo": "CONCENTRACION_ALTA",
            "mensaje": f"Concentración superior al {concentracion['umbral_pct']}% en un proveedor",
            "severidad": "MEDIA",
        })

    estimado = calcular_desviacion(db, org_id)
    if estimado.get("desviacion_pct") and abs(estimado["desviacion_pct"]) > 10:
        alertas.append({
            "tipo": "DESVIACION_COSTO",
            "mensaje": f"Desviación estimado vs real: {estimado['desviacion_pct']:.1f}%",
            "severidad": "MEDIA",
        })

    for alerta in alertas:
        db.add(
            TcoAlertaEconomica(
                organization_id=org_id,
                tipo=alerta["tipo"],
                severidad=alerta["severidad"],
                mensaje=alerta["mensaje"],
                datos_json=_json(alerta),
            )
        )
    return alertas


def calcular_desviacion(db: Session, org_id: str) -> dict[str, Any]:
    est = (
        db.query(func.coalesce(func.sum(TcoCosto.monto), 0))
        .filter(TcoCosto.organization_id == org_id, TcoCosto.naturaleza == NaturalezaCosto.ESTIMADO, TcoCosto.is_active.is_(True))
        .scalar()
    )
    real = (
        db.query(func.coalesce(func.sum(TcoCosto.monto), 0))
        .filter(TcoCosto.organization_id == org_id, TcoCosto.naturaleza == NaturalezaCosto.REAL, TcoCosto.is_active.is_(True))
        .scalar()
    )
    est_d = _decimal(est, Decimal("0")) or Decimal("0")
    real_d = _decimal(real, Decimal("0")) or Decimal("0")
    desviacion = real_d - est_d
    desviacion_pct = float(desviacion / est_d * 100) if est_d > 0 else 0.0
    return {
        "estimado": float(est_d),
        "real": float(real_d),
        "desviacion": float(desviacion),
        "desviacion_pct": desviacion_pct,
    }


# --- Rentabilidad ---

def calcular_rentabilidad(db: Session, org_id: str, params: dict[str, Any]) -> dict[str, Any]:
    tco_est = calcular_tco(db, org_id, {"tipo": NaturalezaCosto.ESTIMADO, "incluir_finops": True}, None)
    tco_real = calcular_tco(db, org_id, {"tipo": NaturalezaCosto.REAL, "incluir_finops": True}, None)
    ingreso_est = _decimal(params.get("ingreso_estimado"))
    ingreso_real = _decimal(params.get("ingreso_real"))
    if ingreso_est is None:
        prop = (
            db.query(CommercialProposal)
            .filter(CommercialProposal.organization_id == org_id, CommercialProposal.estado.in_(["APROBADA", "VIGENTE"]))
            .order_by(CommercialProposal.updated_at.desc())
            .first()
        )
        if prop:
            ingreso_est = prop.precio_final or prop.precio_sugerido
    margen_est = None
    margen_real = None
    if ingreso_est:
        margen_est = float(ingreso_est) - tco_est["total"]
    if ingreso_real:
        margen_real = float(ingreso_real) - tco_real["total"]
    return {
        "ingreso_estimado": float(ingreso_est) if ingreso_est else None,
        "ingreso_real": float(ingreso_real) if ingreso_real else None,
        "tco_estimado": tco_est["total"],
        "tco_real": tco_real["total"],
        "margen_estimado": margen_est,
        "margen_real": margen_real,
        "desviacion": calcular_desviacion(db, org_id),
        "tendencia": "ESTABLE" if abs(calcular_desviacion(db, org_id).get("desviacion_pct", 0)) < 5 else "DESVIACION",
    }


# --- Simulaciones ---

def simular(db: Session, org_id: str, tipo: str, parametros: dict[str, Any], user_id: str | None) -> dict[str, Any]:
    if tipo not in TipoSimulacion.ALL:
        raise TcoValidationError(f"Tipo de simulación inválido: {tipo}")
    base = calcular_tco(db, org_id, {"tipo": NaturalezaCosto.ESTIMADO, "incluir_finops": True}, None)
    resultado: dict[str, Any]
    if tipo == TipoSimulacion.MAKE_OR_BUY:
        resultado = _simular_make_or_buy(parametros)
    elif tipo == TipoSimulacion.SUSTITUCION_PROVEEDOR:
        resultado = _simular_sustitucion(db, org_id, parametros)
    elif tipo == TipoSimulacion.CAMBIO_TARIFA:
        resultado = _simular_cambio_tarifa(db, org_id, parametros, base)
    elif tipo == TipoSimulacion.AUMENTO_CONSUMO:
        factor = _decimal(parametros.get("factor", 1.2), Decimal("1.2")) or Decimal("1.2")
        resultado = {
            "tco_base": base["total"],
            "tco_simulado": base["total"] * float(factor),
            "diferencia": base["total"] * (float(factor) - 1),
            "explicacion": f"Consumo aumentado {float(factor)*100-100:.0f}%",
        }
    else:
        ajuste = float(parametros.get("ajuste_pct", 0))
        resultado = {
            "tco_base": base["total"],
            "tco_simulado": base["total"] * (1 + ajuste / 100),
            "diferencia": base["total"] * ajuste / 100,
            "explicacion": f"Escenario {tipo} con ajuste {ajuste}%",
        }
    row = TcoSimulacion(
        organization_id=org_id,
        tipo=tipo,
        parametros_json=_json(parametros),
        resultado_json=_json(resultado),
        confirmada=False,
        created_by=user_id,
    )
    db.add(row)
    db.flush()
    _audit(db, org_id, "SIMULACION", "simulacion", row.id, user_id, {"tipo": tipo})
    resultado["simulacion_id"] = row.id
    resultado["es_simulacion"] = True
    return resultado


def _simular_make_or_buy(p: dict[str, Any]) -> dict[str, Any]:
    ci = float(p.get("costo_interno", 0))
    ct = float(p.get("costo_tercero", 0))
    mi = float(p.get("mantenimiento_interno_anual", 0))
    mt = float(p.get("mantenimiento_tercero_anual", 0))
    ti = float(p.get("tiempo_interno_meses", 6))
    tt = float(p.get("tiempo_tercero_meses", 3))
    ri = _RIESGO_SCORE.get(p.get("riesgo_interno", "MEDIO"), 2)
    rt = _RIESGO_SCORE.get(p.get("riesgo_tercero", "BAJO"), 1)
    costo_total_interno = ci + mi * (ti / 12)
    costo_total_tercero = ct + mt * (tt / 12)
    recomendacion = "TERCERO" if costo_total_tercero < costo_total_interno and rt <= ri else "INTERNO"
    return {
        "costo_interno_total": costo_total_interno,
        "costo_tercero_total": costo_total_tercero,
        "diferencia": costo_total_interno - costo_total_tercero,
        "tiempo_interno_meses": ti,
        "tiempo_tercero_meses": tt,
        "riesgo_interno": p.get("riesgo_interno"),
        "riesgo_tercero": p.get("riesgo_tercero"),
        "recomendacion_explicativa": f"Opción sugerida: {recomendacion} (no ejecuta decisión automática)",
        "explicacion": f"Hacer internamente: {costo_total_interno:,.0f}; Contratar tercero: {costo_total_tercero:,.0f}",
    }


def _simular_sustitucion(db: Session, org_id: str, p: dict[str, Any]) -> dict[str, Any]:
    actual = get_proveedor(db, org_id, p["proveedor_actual_id"])
    alternativo = get_proveedor(db, org_id, p["proveedor_alternativo_id"])
    unidades = _decimal(p.get("unidades_mensuales", 1_000_000), Decimal("1000000")) or Decimal("1000000")
    tarifas_act = list_tarifas(db, org_id, actual.id)
    tarifas_alt = list_tarifas(db, org_id, alternativo.id)
    costo_act = Decimal("0")
    costo_alt = Decimal("0")
    if tarifas_act and tarifas_act[0].get("tramos"):
        costo_act = calcular_tarifa_volumen(tarifas_act[0]["tramos"], unidades)["costo"]
    elif tarifas_act and tarifas_act[0].get("monto_base"):
        costo_act = _decimal(tarifas_act[0]["monto_base"], Decimal("0")) or Decimal("0")
    if tarifas_alt and tarifas_alt[0].get("tramos"):
        costo_alt = calcular_tarifa_volumen(tarifas_alt[0]["tramos"], unidades)["costo"]
    elif tarifas_alt and tarifas_alt[0].get("monto_base"):
        costo_alt = _decimal(tarifas_alt[0]["monto_base"], Decimal("0")) or Decimal("0")
    ahorro = float(costo_act - costo_alt)
    return {
        "proveedor_actual": actual.nombre,
        "proveedor_alternativo": alternativo.nombre,
        "costo_actual": float(costo_act),
        "costo_alternativo": float(costo_alt),
        "ahorro_esperado": ahorro,
        "sla_actual": p.get("sla_actual"),
        "sla_alternativo": p.get("sla_alternativo"),
        "riesgo_actual": actual.riesgo_nivel,
        "riesgo_alternativo": alternativo.riesgo_nivel,
        "explicacion": f"Sustitución {actual.nombre} → {alternativo.nombre}: ahorro {ahorro:,.2f}",
    }


def _simular_cambio_tarifa(db: Session, org_id: str, p: dict[str, Any], base: dict[str, Any]) -> dict[str, Any]:
    nueva_tarifa = float(p.get("nueva_tarifa_mensual", 0))
    tarifa_actual = float(p.get("tarifa_actual_mensual", base["total"]))
    return {
        "tco_base": base["total"],
        "tarifa_actual": tarifa_actual,
        "nueva_tarifa": nueva_tarifa,
        "diferencia": nueva_tarifa - tarifa_actual,
        "explicacion": f"Cambio de tarifa: {tarifa_actual:,.0f} → {nueva_tarifa:,.0f}",
    }


def comparar_proveedores(db: Session, org_id: str, proveedor_ids: list[str], unidades: float) -> list[dict[str, Any]]:
    unidades_d = _decimal(unidades, Decimal("1")) or Decimal("1")
    resultados = []
    for pid in proveedor_ids:
        prov = get_proveedor(db, org_id, pid)
        tarifas = list_tarifas(db, org_id, pid)
        costo = Decimal("0")
        if tarifas:
            t = tarifas[0]
            if t.get("tramos"):
                costo = calcular_tarifa_volumen(t["tramos"], unidades_d)["costo"]
            elif t.get("monto_base"):
                costo = _decimal(t["monto_base"], Decimal("0")) or Decimal("0")
        contratos = list_contratos(db, org_id, pid)
        sla = contratos[0].sla if contratos else None
        resultados.append({
            "proveedor_id": pid,
            "nombre": prov.nombre,
            "costo": float(costo),
            "sla": sla,
            "riesgo": prov.riesgo_nivel,
            "tipo": prov.tipo,
        })
    resultados.sort(key=lambda x: x["costo"])
    return resultados


# --- Alianzas ---

def create_alianza(db: Session, org_id: str, data: dict[str, Any], user_id: str | None) -> TcoAlianza:
    if data.get("proveedor_id"):
        get_proveedor(db, org_id, data["proveedor_id"])
    row = TcoAlianza(
        organization_id=org_id,
        proveedor_id=data.get("proveedor_id"),
        opportunity_id=data.get("opportunity_id"),
        nombre=data["nombre"],
        tipo=data["tipo"],
        objetivo=data.get("objetivo"),
        alcance=data.get("alcance"),
        vigencia_desde=data.get("vigencia_desde"),
        vigencia_hasta=data.get("vigencia_hasta"),
        beneficios_esperados=data.get("beneficios_esperados"),
        costos_esperados=_decimal(data.get("costos_esperados")),
        responsabilidades=data.get("responsabilidades"),
    )
    db.add(row)
    db.flush()
    _audit(db, org_id, "CREAR", "alianza", row.id, user_id, {"nombre": row.nombre})
    return row


def alianza_to_dict(row: TcoAlianza) -> dict[str, Any]:
    return {
        "id": row.id,
        "nombre": row.nombre,
        "tipo": row.tipo,
        "proveedor_id": row.proveedor_id,
        "opportunity_id": row.opportunity_id,
        "objetivo": row.objetivo,
        "estado": row.estado,
        "costos_esperados": float(row.costos_esperados) if row.costos_esperados else None,
        "vigencia_desde": row.vigencia_desde.isoformat() if row.vigencia_desde else None,
        "vigencia_hasta": row.vigencia_hasta.isoformat() if row.vigencia_hasta else None,
    }


def list_alianzas(db: Session, org_id: str) -> list[dict[str, Any]]:
    rows = db.query(TcoAlianza).filter(TcoAlianza.organization_id == org_id).order_by(TcoAlianza.nombre).all()
    return [alianza_to_dict(r) for r in rows]


def update_alianza_estado(db: Session, org_id: str, alianza_id: str, estado: str, user_id: str | None, justificacion: str | None = None) -> TcoAlianza:
    row = db.query(TcoAlianza).filter(TcoAlianza.id == alianza_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Alianza no encontrada")
    _ensure_org_scope(db, org_id, row.organization_id)
    row.estado = estado
    db.flush()
    _audit(db, org_id, "CAMBIO_ESTADO", "alianza", row.id, user_id, {"estado": estado, "justificacion": justificacion})
    return row


# --- Centro de control adapter ---

def centro_control_resumen(db: Session, org_id: str) -> dict[str, Any]:
    tco = calcular_tco(db, org_id, {"tipo": NaturalezaCosto.ESTIMADO, "incluir_finops": True}, None)
    rent = calcular_rentabilidad(db, org_id, {})
    alertas = (
        db.query(TcoAlertaEconomica)
        .filter(TcoAlertaEconomica.organization_id == org_id, TcoAlertaEconomica.resuelta.is_(False))
        .order_by(TcoAlertaEconomica.created_at.desc())
        .limit(10)
        .all()
    )
    return {
        "tco_total": tco["total"],
        "desglose": tco["desglose"],
        "margen_pct": tco.get("margen_pct"),
        "desviacion": rent["desviacion"],
        "proveedores_criticos": [p for p in tco["proveedores"] if p.get("pct", 0) > 20],
        "concentracion": tco["concentracion"],
        "alertas": [{"tipo": a.tipo, "mensaje": a.mensaje, "severidad": a.severidad} for a in alertas],
    }


# --- Historial ---

def list_historial(db: Session, org_id: str) -> dict[str, Any]:
    snapshots = (
        db.query(TcoSnapshot)
        .filter(TcoSnapshot.organization_id == org_id)
        .order_by(TcoSnapshot.created_at.desc())
        .limit(50)
        .all()
    )
    simulaciones = (
        db.query(TcoSimulacion)
        .filter(TcoSimulacion.organization_id == org_id)
        .order_by(TcoSimulacion.created_at.desc())
        .limit(50)
        .all()
    )
    auditoria = (
        db.query(TcoAuditoria)
        .filter(TcoAuditoria.organization_id == org_id)
        .order_by(TcoAuditoria.created_at.desc())
        .limit(50)
        .all()
    )
    return {
        "snapshots": [
            {"id": s.id, "periodo": s.periodo, "total": float(s.total), "tipo": s.tipo, "created_at": s.created_at.isoformat()}
            for s in snapshots
        ],
        "simulaciones": [
            {"id": s.id, "tipo": s.tipo, "confirmada": s.confirmada, "created_at": s.created_at.isoformat()}
            for s in simulaciones
        ],
        "auditoria": [
            {"id": a.id, "accion": a.accion, "entidad": a.entidad, "created_at": a.created_at.isoformat()}
            for a in auditoria
        ],
    }
