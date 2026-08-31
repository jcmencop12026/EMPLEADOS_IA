"""Servicio — Continuidad comercial y operacional EIAAX (1720)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.commercial_enums import ProposalStatus
from app.commercial_models import CommercialProposal, CommercialProposalValue
from app.continuidad_comercial_enums import (
    AceptacionEntregable,
    EstadoCambioAlcance,
    EstadoCierreContrato,
    EstadoEntregable,
)
from app.continuidad_comercial_models import ContinuidadCambioAlcance, NegocioContractClosure
from app.evaluacion_models import EvaluacionExpediente
from app.implementacion_models import ImplementacionProyecto
from app.models import User
from app.negocio_enums import PerspectivaPropuesta, ProposalVersionTrigger
from app.negocio_models import (
    NegocioContractRecord,
    NegocioNegotiationEntry,
    NegocioProposalExtension,
    NegocioProposalVersion,
)
from app.opportunity_models import Opportunity
from app.services import commercial_service as com_svc
from app.services import continuidad_finops_bridge as finops_bridge
from app.services.continuidad_resultado_port import get_resultado_adapter
from app.services import implementacion_service as impl_svc
from app.services import negocio_service as neg_svc


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, default=str)


def _parse(raw: str | None) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _next_cambio_codigo(db: Session, org_id: str) -> str:
    n = (
        db.query(func.count(ContinuidadCambioAlcance.id))
        .filter(ContinuidadCambioAlcance.organization_id == org_id)
        .scalar()
        or 0
    )
    return f"CAMBIO-{n + 1:04d}"


def _next_opp_codigo(db: Session, org_id: str) -> str:
    n = db.query(func.count(Opportunity.id)).filter(Opportunity.organization_id == org_id).scalar() or 0
    return f"OPP-{n + 1:05d}"


def build_compromiso_contractual_snapshot(
    db: Session,
    *,
    proposal: CommercialProposal,
    ext: NegocioProposalExtension,
    contract: NegocioContractRecord | None,
    version: NegocioProposalVersion | None,
) -> dict[str, Any]:
    """Snapshot inmutable contractual — referencias + datos congelados al convertir."""
    perspectivas = _parse(ext.perspectivas_json) or neg_svc._default_perspectives(proposal, ext)
    operaciones = perspectivas.get(PerspectivaPropuesta.OPERACIONES, {})
    valores = (
        db.query(CommercialProposalValue)
        .filter(CommercialProposalValue.proposal_id == proposal.id)
        .all()
    )
    indicadores = operaciones.get("indicadores") or []
    return {
        "referencias": {
            "proposal_id": proposal.id,
            "proposal_codigo": proposal.codigo,
            "opportunity_id": ext.opportunity_id,
            "evaluacion_id": ext.evaluacion_id,
            "contract_id": contract.id if contract else None,
            "version_number": version.version_number if version else ext.version_actual,
            "document_id": (contract.document_id if contract else None) or (version.pdf_document_id if version else None),
            "finops_budget_id": contract.finops_budget_id if contract else None,
        },
        "contrato": {
            "precio_contratado": float(contract.precio_contratado) if contract and contract.precio_contratado else float(ext.precio_contratado or 0) or None,
            "modelo_comercial": (contract.modelo_comercial if contract else None) or ext.modelo_comercial,
            "condiciones": contract.condiciones if contract else None,
            "fecha_contratacion": contract.fecha_contratacion.isoformat() if contract and contract.fecha_contratacion else None,
        },
        "alcance_contratado": {
            "titulo": proposal.titulo,
            "alcance": operaciones.get("solucion") or proposal.titulo,
            "procesos_afectados": operaciones.get("procesos_afectados"),
            "cambio_operacional": operaciones.get("cambio_operacional"),
            "implementacion": operaciones.get("implementacion"),
            "exclusiones": _parse(proposal.supuestos_json),
            "supuestos": _parse(proposal.supuestos_json),
        },
        "indicadores_comprometidos": indicadores,
        "consumo_ia": _parse(ext.ia_consumo_json),
        "documento_cliente": _parse(ext.documento_cliente_json) or (version and _parse(version.documento_cliente_json)),
        "valores_linea": [
            {
                "categoria": v.categoria,
                "monto": float(v.valor_bruto) if v.valor_bruto else None,
                "naturaleza": v.naturaleza,
            }
            for v in valores
        ],
        "economia_cliente": {
            "valor_total_esperado": float(proposal.valor_total_esperado) if proposal.valor_total_esperado else None,
            "valor_atribuible_total": float(proposal.valor_atribuible_total) if proposal.valor_atribuible_total else None,
            "precio_final": float(proposal.precio_final) if proposal.precio_final else None,
            "roi_pct": float(proposal.roi_pct) if proposal.roi_pct else None,
            "payback_meses": float(proposal.payback_meses) if proposal.payback_meses else None,
        },
        "snapshot_at": _utcnow().isoformat(),
    }


def ensure_contract_record(
    db: Session,
    user: User,
    org_id: str,
    proposal_id: str,
    *,
    condiciones: str | None = None,
) -> NegocioContractRecord:
    """B03 — Garantiza registro contractual si propuesta ya está ACEPTADA."""
    existing = (
        db.query(NegocioContractRecord)
        .filter(NegocioContractRecord.proposal_id == proposal_id, NegocioContractRecord.organization_id == org_id)
        .order_by(NegocioContractRecord.fecha_contratacion.desc())
        .first()
    )
    if existing:
        return existing
    result = neg_svc.contract_proposal(db, user, org_id, proposal_id, condiciones=condiciones)
    return db.query(NegocioContractRecord).filter(NegocioContractRecord.id == result["contract_id"]).first()


def enrich_proyecto_from_contrato(
    db: Session,
    proyecto: ImplementacionProyecto,
    *,
    proposal: CommercialProposal,
    ext: NegocioProposalExtension,
    contract: NegocioContractRecord,
    version: NegocioProposalVersion | None,
) -> None:
    """B01/B02 — Persiste compromiso real y referencias canónicas."""
    snapshot = build_compromiso_contractual_snapshot(db, proposal=proposal, ext=ext, contract=contract, version=version)
    alcance_data = snapshot.get("alcance_contratado") or {}
    alcance_parts = [alcance_data.get("alcance") or proposal.titulo]
    if alcance_data.get("procesos_afectados"):
        alcance_parts.append(f"Procesos: {alcance_data['procesos_afectados']}")
    if snapshot.get("contrato", {}).get("condiciones"):
        alcance_parts.append(f"Condiciones: {snapshot['contrato']['condiciones']}")

    proyecto.opportunity_id = ext.opportunity_id
    proyecto.evaluacion_id = ext.evaluacion_id
    proyecto.contract_id = contract.id
    proyecto.version_contratada = version.version_number if version else contract.version_number
    proyecto.documento_contrato_id = contract.document_id or (version.pdf_document_id if version else None)
    proyecto.compromiso_contractual_json = _json(snapshot)
    proyecto.alcance = "\n".join(str(p) for p in alcance_parts if p)
    proyecto.objetivos = ext.proximo_paso or snapshot.get("alcance_contratado", {}).get("implementacion")
    proyecto.finops_budget_id = contract.finops_budget_id
    compromiso = impl_svc._snapshot_valor_compromiso(db, proposal.id)
    if compromiso:
        proyecto.valor_compromiso_json = _json(compromiso)


def create_opportunity_from_continuidad(
    db: Session,
    org_id: str,
    *,
    titulo: str,
    descripcion: str,
    tipo: str,
    proyecto_id: str | None = None,
    proposal_id: str | None = None,
    origen: str = "RENOVACION",
) -> Opportunity:
    """B08 — Crea oportunidad 1030 sin duplicar si ya existe enlace."""
    ext = None
    if proposal_id:
        ext = db.query(NegocioProposalExtension).filter(NegocioProposalExtension.proposal_id == proposal_id).first()
        if ext and ext.opportunity_id:
            existing = (
                db.query(Opportunity)
                .filter(Opportunity.id == ext.opportunity_id, Opportunity.organization_id == org_id)
                .first()
            )
            if existing and existing.estado not in ("CERRADA", "DESCARTADA"):
                return existing

    opp = Opportunity(
        organization_id=org_id,
        codigo=_next_opp_codigo(db, org_id),
        tipo=tipo,
        dominio="COMERCIAL",
        titulo=titulo,
        descripcion=descripcion,
        contexto_json=_json({"origen": origen, "proyecto_id": proyecto_id, "proposal_id": proposal_id}),
        estado="DETECTADA",
        urgencia="MEDIA",
        confianza=0.8,
    )
    db.add(opp)
    db.flush()
    return opp


def vista_continuidad(
    db: Session,
    org_id: str,
    *,
    proposal_id: str | None = None,
    contract_id: str | None = None,
    proyecto_id: str | None = None,
    include_private: bool = False,
) -> dict[str, Any]:
    """B09 — Vista compromiso → resultado sin recalcular."""
    proposal = None
    ext = None
    contract = None
    proyecto = None

    if proyecto_id:
        proyecto = db.query(ImplementacionProyecto).filter(
            ImplementacionProyecto.id == proyecto_id,
            ImplementacionProyecto.organization_id == org_id,
        ).first()
        if not proyecto:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        proposal_id = proposal_id or proyecto.proposal_id
        contract_id = contract_id or proyecto.contract_id

    if contract_id:
        contract = db.query(NegocioContractRecord).filter(
            NegocioContractRecord.id == contract_id,
            NegocioContractRecord.organization_id == org_id,
        ).first()
        if contract:
            proposal_id = proposal_id or contract.proposal_id

    if proposal_id:
        proposal = com_svc._get_proposal(db, org_id, proposal_id)
        ext = db.query(NegocioProposalExtension).filter(NegocioProposalExtension.proposal_id == proposal_id).first()

    if not proposal:
        raise HTTPException(status_code=404, detail="Propuesta no encontrada")

    if not proyecto and ext and ext.implementacion_proyecto_id:
        proyecto = db.query(ImplementacionProyecto).filter(ImplementacionProyecto.id == ext.implementacion_proyecto_id).first()

    diagnostico = None
    if ext and ext.evaluacion_id:
        ev = db.query(EvaluacionExpediente).filter(
            EvaluacionExpediente.id == ext.evaluacion_id,
            EvaluacionExpediente.organization_id == org_id,
        ).first()
        if ev:
            diagnostico = {"id": ev.id, "codigo": ev.codigo, "titulo": ev.titulo, "estado": ev.estado}

    compromiso = _parse(proyecto.compromiso_contractual_json) if proyecto else None
    if not compromiso and ext:
        ver = (
            db.query(NegocioProposalVersion)
            .filter(NegocioProposalVersion.proposal_id == proposal_id)
            .order_by(NegocioProposalVersion.version_number.desc())
            .first()
        )
        compromiso = build_compromiso_contractual_snapshot(
            db, proposal=proposal, ext=ext, contract=contract, version=ver
        )

    resultado_adapter = get_resultado_adapter()
    real = resultado_adapter.fetch_real(
        db,
        org_id,
        opportunity_id=ext.opportunity_id if ext else None,
        proyecto_id=proyecto.id if proyecto else None,
        include_private=include_private,
    )

    finops = None
    if contract and ext:
        finops = finops_bridge.contract_finops_summary(db, contract, ext)

    return {
        "diagnosticado": diagnostico,
        "prometido": {
            "propuesta": {"id": proposal.id, "codigo": proposal.codigo, "titulo": proposal.titulo},
            "perspectivas": _parse(ext.perspectivas_json) if ext else None,
            "documento_cliente": _parse(ext.documento_cliente_json) if ext else None,
        },
        "contratado": compromiso.get("contrato") if compromiso else None,
        "compromiso_snapshot": compromiso,
        "implementado": {
            "proyecto_id": proyecto.id if proyecto else None,
            "codigo": proyecto.codigo if proyecto else None,
            "estado": proyecto.estado if proyecto else None,
            "alcance": proyecto.alcance if proyecto else None,
            "go_live": proyecto.go_live_aprobado if proyecto else None,
        },
        "operando": {
            "finops": finops,
            "finops_budget_id": proyecto.finops_budget_id if proyecto else (contract.finops_budget_id if contract else None),
        },
        "proyectado": {
            "valor_total_esperado": float(proposal.valor_total_esperado) if proposal.valor_total_esperado else None,
            "roi_pct": float(proposal.roi_pct) if proposal.roi_pct else None,
        },
        "resultado_real": real,
        "referencias": {
            "proposal_id": proposal.id,
            "opportunity_id": ext.opportunity_id if ext else None,
            "evaluacion_id": ext.evaluacion_id if ext else None,
            "contract_id": contract.id if contract else None,
            "proyecto_id": proyecto.id if proyecto else None,
        },
    }


# --- Cambios de alcance ---

def create_cambio_alcance(
    db: Session,
    user: User,
    org_id: str,
    data: dict[str, Any],
) -> ContinuidadCambioAlcance:
    proposal = com_svc._get_proposal(db, org_id, data["proposal_id"])
    if proposal.estado not in (ProposalStatus.ACEPTADA, ProposalStatus.ENVIADA):
        raise HTTPException(status_code=422, detail="Cambio de alcance requiere propuesta contratada o en curso")
    proyecto = None
    if data.get("proyecto_id"):
        proyecto = impl_svc._get_proyecto(db, org_id, data["proyecto_id"])
    contract = None
    if data.get("contract_id"):
        contract = db.query(NegocioContractRecord).filter(
            NegocioContractRecord.id == data["contract_id"],
            NegocioContractRecord.organization_id == org_id,
        ).first()
    row = ContinuidadCambioAlcance(
        organization_id=org_id,
        codigo=_next_cambio_codigo(db, org_id),
        proposal_id=proposal.id,
        proyecto_id=proyecto.id if proyecto else data.get("proyecto_id"),
        contract_id=contract.id if contract else data.get("contract_id"),
        solicitud=data["solicitud"],
        created_by_id=user.id,
    )
    db.add(row)
    db.flush()
    write_audit(
        db,
        action="continuidad.cambio.solicitado",
        organization_id=org_id,
        user_id=user.id,
        detail=_json({"cambio_id": row.id, "codigo": row.codigo}),
        commit=False,
    )
    return row


def avanzar_cambio_alcance(
    db: Session,
    user: User,
    org_id: str,
    cambio_id: str,
    *,
    accion: str,
    payload: dict[str, Any],
) -> ContinuidadCambioAlcance:
    row = db.query(ContinuidadCambioAlcance).filter(
        ContinuidadCambioAlcance.id == cambio_id,
        ContinuidadCambioAlcance.organization_id == org_id,
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Cambio de alcance no encontrado")

    if accion == "analizar":
        row.estado = EstadoCambioAlcance.EN_ANALISIS
        row.analisis = payload.get("analisis")
    elif accion == "impacto":
        row.estado = EstadoCambioAlcance.IMPACTO_EVALUADO
        row.impacto_json = _json(payload.get("impacto") or payload)
    elif accion == "decidir":
        row.estado = EstadoCambioAlcance.DECIDIDO
        row.decision = payload.get("decision")
        if payload.get("aprobado"):
            row.estado = EstadoCambioAlcance.APROBADO
        elif payload.get("rechazado"):
            row.estado = EstadoCambioAlcance.RECHAZADO
    elif accion == "implementar":
        row.estado = EstadoCambioAlcance.IMPLEMENTANDO
        if payload.get("crear_version_comercial"):
            ver = neg_svc.create_version_snapshot(
                db, user, org_id, row.proposal_id, trigger=ProposalVersionTrigger.NEGOCIACION
            )
            row.nueva_version_id = ver.id
            entry = NegocioNegotiationEntry(
                proposal_id=row.proposal_id,
                organization_id=org_id,
                cambios_solicitados=row.solicitud,
                observaciones=row.decision,
                proximo_paso="Implementar cambio aprobado",
                estado="CERRADA",
                created_by_id=user.id,
            )
            db.add(entry)
            db.flush()
            row.negociacion_entry_id = entry.id
    elif accion == "cerrar":
        row.estado = EstadoCambioAlcance.CERRADO
    else:
        raise HTTPException(status_code=400, detail=f"Acción no válida: {accion}")

    row.updated_at = _utcnow()
    db.flush()
    return row


def cambio_to_dict(row: ContinuidadCambioAlcance) -> dict[str, Any]:
    return {
        "id": row.id,
        "codigo": row.codigo,
        "estado": row.estado,
        "proposal_id": row.proposal_id,
        "proyecto_id": row.proyecto_id,
        "contract_id": row.contract_id,
        "solicitud": row.solicitud,
        "analisis": row.analisis,
        "decision": row.decision,
        "impacto": _parse(row.impacto_json),
        "nueva_version_id": row.nueva_version_id,
        "negociacion_entry_id": row.negociacion_entry_id,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


# --- Offboarding / cierre contractual ---

def iniciar_cierre_contrato(
    db: Session,
    user: User,
    org_id: str,
    contract_id: str,
    data: dict[str, Any],
) -> NegocioContractClosure:
    contract = db.query(NegocioContractRecord).filter(
        NegocioContractRecord.id == contract_id,
        NegocioContractRecord.organization_id == org_id,
    ).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    existing = (
        db.query(NegocioContractClosure)
        .filter(NegocioContractClosure.contract_id == contract_id, NegocioContractClosure.estado != EstadoCierreContrato.COMPLETADO)
        .first()
    )
    if existing:
        return existing
    ext = db.query(NegocioProposalExtension).filter(NegocioProposalExtension.proposal_id == contract.proposal_id).first()
    row = NegocioContractClosure(
        organization_id=org_id,
        contract_id=contract_id,
        proposal_id=contract.proposal_id,
        proyecto_id=ext.implementacion_proyecto_id if ext else data.get("proyecto_id"),
        motivo=data["motivo"],
        pendientes_json=_json(data.get("pendientes")),
        empleados_retirar_json=_json(data.get("empleados_retirar")),
        accesos_retirar_json=_json(data.get("accesos_retirar")),
        exportaciones_json=_json(data.get("exportaciones")),
        observaciones=data.get("observaciones"),
        created_by_id=user.id,
    )
    db.add(row)
    db.flush()
    write_audit(
        db,
        action="continuidad.cierre.iniciado",
        organization_id=org_id,
        user_id=user.id,
        detail=_json({"closure_id": row.id, "contract_id": contract_id}),
        commit=False,
    )
    return row


def confirmar_cierre_contrato(
    db: Session,
    user: User,
    org_id: str,
    closure_id: str,
    *,
    confirmacion: bool = True,
) -> NegocioContractClosure:
    row = db.query(NegocioContractClosure).filter(
        NegocioContractClosure.id == closure_id,
        NegocioContractClosure.organization_id == org_id,
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Cierre no encontrado")
    row.confirmacion = confirmacion
    row.estado = EstadoCierreContrato.COMPLETADO if confirmacion else EstadoCierreContrato.EN_PROCESO
    row.fecha_cierre = _utcnow() if confirmacion else row.fecha_cierre
    if row.proyecto_id and confirmacion:
        try:
            impl_svc.update_proyecto(db, org_id, row.proyecto_id, {"estado": "CERRADO"}, user.id)
        except Exception:
            pass
    db.flush()
    write_audit(
        db,
        action="continuidad.cierre.confirmado",
        organization_id=org_id,
        user_id=user.id,
        detail=_json({"closure_id": row.id}),
        commit=False,
    )
    return row


def closure_to_dict(row: NegocioContractClosure) -> dict[str, Any]:
    return {
        "id": row.id,
        "contract_id": row.contract_id,
        "proposal_id": row.proposal_id,
        "proyecto_id": row.proyecto_id,
        "motivo": row.motivo,
        "fecha_cierre": row.fecha_cierre.isoformat() if row.fecha_cierre else None,
        "estado": row.estado,
        "pendientes": _parse(row.pendientes_json),
        "empleados_retirar": _parse(row.empleados_retirar_json),
        "accesos_retirar": _parse(row.accesos_retirar_json),
        "exportaciones": _parse(row.exportaciones_json),
        "confirmacion": row.confirmacion,
        "observaciones": row.observaciones,
    }
