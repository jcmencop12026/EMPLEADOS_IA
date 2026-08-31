"""Servicio — Centro de Negocios EIAAX (orquestación 1280/1210/1405/1600)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.commercial_enums import ProposalStatus, ValueNature
from app.commercial_models import CommercialProposal
from app.models import User
from app.negocio_enums import (
    PROPOSAL_TRANSITIONS,
    ModeloComercial,
    PerspectivaPropuesta,
    PriceDecisionAction,
    PricePhase,
    ProposalVersionTrigger,
)
from app.negocio_models import (
    NegocioContractRecord,
    NegocioNegotiationEntry,
    NegocioPriceDecision,
    NegocioPricePhaseRecord,
    NegocioProposalDocument,
    NegocioProposalExtension,
    NegocioProposalVersion,
)
from app.negocio_labels import label_proposal_status
from app.opportunity_models import Opportunity
from app.services import commercial_service as com_svc
from app.services import control_center_service as cc_svc
from app.services import economic_motor_service as motor_svc
from app.services import implementacion_service as impl_svc
from app.services import proactive_service as opp_svc
from app.services.negocio_approval_adapter import get_approval_adapter, list_approval_status
from app.services.negocio_pdf_service import generate_and_store_pdf
from app.services import negocio_sync_service as sync_svc
from app.services import continuidad_finops_bridge as cont_finops
from app.services import continuidad_comercial_service as cont_svc

POTENCIAL_NOTE = "POTENCIAL no cuenta como beneficio realizado ni en ROI/payback realizado."


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


def resolve_organization_id(db: Session, user: User, requested_org_id: str | None) -> str:
    return cc_svc.resolve_organization_id(db, user, requested_org_id)


def _get_extension(db: Session, proposal_id: str, org_id: str) -> NegocioProposalExtension:
    ext = (
        db.query(NegocioProposalExtension)
        .filter(
            NegocioProposalExtension.proposal_id == proposal_id,
            NegocioProposalExtension.organization_id == org_id,
        )
        .first()
    )
    if not ext:
        raise HTTPException(status_code=404, detail="Extensión de negocio no encontrada")
    return ext


def _ensure_extension(db: Session, proposal: CommercialProposal) -> NegocioProposalExtension:
    ext = db.query(NegocioProposalExtension).filter(NegocioProposalExtension.proposal_id == proposal.id).first()
    if ext:
        return ext
    ext = NegocioProposalExtension(
        proposal_id=proposal.id,
        organization_id=proposal.organization_id,
    )
    db.add(ext)
    db.flush()
    return ext


def _default_perspectives(proposal: CommercialProposal, ext: NegocioProposalExtension | None) -> dict[str, Any]:
    titulo = proposal.titulo
    return {
        PerspectivaPropuesta.GERENCIA: {
            "situacion": f"Propuesta {proposal.codigo}: {titulo}",
            "oportunidad": "Oportunidad de mejora identificada en evaluación EIAAX",
            "impacto": float(proposal.valor_atribuible_total or 0) if proposal.valor_atribuible_total else None,
            "valor_realizado": None,
            "valor_potencial": None,
            "roi": float(proposal.roi_pct) if proposal.roi_pct else None,
            "inversion": float(proposal.precio_final or proposal.precio_sugerido or 0) or None,
            "resultados_esperados": _parse(proposal.supuestos_json),
            "nota_potencial": POTENCIAL_NOTE,
        },
        PerspectivaPropuesta.OPERACIONES: {
            "procesos_afectados": [],
            "solucion": titulo,
            "automatizacion": "Empleados IA y capacidades transversales",
            "cambio_operacional": _parse(proposal.supuestos_json),
            "indicadores": [],
            "implementacion": "Fases según alcance acordado",
            "responsabilidades": {},
        },
        PerspectivaPropuesta.SISTEMAS: {
            "arquitectura": "Integración sobre plataforma EMPLEADOS_IA",
            "integraciones": [],
            "seguridad_gobierno": "RBAC multiempresa, auditoría y gobierno de datos",
            "interoperabilidad": "APIs y conectores existentes",
            "continuidad": "Según plan de continuidad organizacional",
            "dependencias": _parse(proposal.riesgos_json),
        },
    }


def _record_price_phase(
    db: Session,
    org_id: str,
    proposal_id: str,
    fase: str,
    monto: float | None,
    user_id: str | None,
    *,
    version_number: int | None = None,
    nota: str | None = None,
) -> None:
    db.add(
        NegocioPricePhaseRecord(
            proposal_id=proposal_id,
            organization_id=org_id,
            fase=fase,
            monto=monto,
            version_number=version_number,
            user_id=user_id,
            nota=nota,
        )
    )


def _client_inversion(proposal: CommercialProposal, ext: NegocioProposalExtension) -> float | None:
    """Solo precio final aprobado — nunca sugerido ni potencial."""
    if proposal.precio_final is not None:
        return float(proposal.precio_final)
    return None


def _build_client_document(proposal: CommercialProposal, ext: NegocioProposalExtension, perspectives: dict) -> dict[str, Any]:
    """Solo campos autorizados para cliente — sin margen ni costos internos."""
    gerencia = perspectives.get(PerspectivaPropuesta.GERENCIA, {})
    return {
        "codigo": proposal.codigo,
        "titulo": proposal.titulo,
        "estado": proposal.estado,
        "version": ext.version_actual,
        "resumen_ejecutivo": gerencia.get("situacion"),
        "situacion": gerencia.get("situacion"),
        "oportunidad": gerencia.get("oportunidad"),
        "solucion": perspectives.get(PerspectivaPropuesta.OPERACIONES, {}).get("solucion"),
        "alcance": _parse(proposal.supuestos_json),
        "exclusiones": [],
        "implementacion": perspectives.get(PerspectivaPropuesta.OPERACIONES, {}).get("implementacion"),
        "cronograma": None,
        "indicadores": perspectives.get(PerspectivaPropuesta.OPERACIONES, {}).get("indicadores"),
        "inversion": _client_inversion(proposal, ext),
        "modalidad_comercial": ext.modelo_comercial,
        "consumo_ia": _parse(ext.ia_consumo_json),
        "soporte_sla": None,
        "supuestos": _parse(proposal.supuestos_json),
        "responsabilidades": perspectives.get(PerspectivaPropuesta.OPERACIONES, {}).get("responsabilidades"),
        "proximos_pasos": ext.proximo_paso,
        "nota_potencial": POTENCIAL_NOTE,
        "economia_privada_incluida": False,
    }


def _build_internal_document(
    db: Session,
    proposal: CommercialProposal,
    ext: NegocioProposalExtension,
) -> dict[str, Any]:
    private = motor_svc.get_private_economy(db, proposal.organization_id)
    private_summary = None
    if private:
        private_summary = {
            "estimated_cost": float(private.estimated_cost) if private.estimated_cost else None,
            "real_cost": float(private.real_cost) if private.real_cost else None,
            "suggested_price": float(private.suggested_price) if private.suggested_price else None,
            "margin": float(private.margin) if private.margin else None,
        }
    return {
        "proposal_id": proposal.id,
        "margen_pct": float(proposal.margen_pct) if proposal.margen_pct else None,
        "costo_total": float(proposal.costo_total) if proposal.costo_total else None,
        "precio_sugerido": float(proposal.precio_sugerido) if proposal.precio_sugerido else None,
        "economic_recommendation_id": ext.economic_recommendation_id,
        "economia_privada_org": private_summary,
        "riesgos": _parse(proposal.riesgos_json),
        "traceability": _parse(proposal.traceability_json),
        "nota": "Documento interno — no publicar al cliente",
    }


def _snapshot_proposal(db: Session, proposal: CommercialProposal, ext: NegocioProposalExtension) -> dict[str, Any]:
    detail = com_svc.proposal_to_detail(db, proposal.organization_id, proposal.id)
    detail["negocio"] = {
        "opportunity_id": ext.opportunity_id,
        "evaluacion_id": ext.evaluacion_id,
        "modelo_comercial": ext.modelo_comercial,
        "version_actual": ext.version_actual,
        "perspectivas": _parse(ext.perspectivas_json),
    }
    return detail


def create_version_snapshot(
    db: Session,
    user: User,
    org_id: str,
    proposal_id: str,
    *,
    trigger: str,
) -> NegocioProposalVersion:
    proposal = com_svc._get_proposal(db, org_id, proposal_id)
    ext = _ensure_extension(db, proposal)
    ext.version_actual += 1
    perspectives = _parse(ext.perspectivas_json) or _default_perspectives(proposal, ext)
    client_doc = _build_client_document(proposal, ext, perspectives)
    snap = _snapshot_proposal(db, proposal, ext)
    ver = NegocioProposalVersion(
        proposal_id=proposal.id,
        organization_id=org_id,
        version_number=ext.version_actual,
        trigger=trigger,
        estado_comercial=proposal.estado,
        snapshot_json=_json(snap),
        documento_cliente_json=_json(client_doc),
        created_by_id=user.id,
    )
    db.add(ver)
    db.flush()
    write_audit(
        db,
        action="negocio.propuesta.version",
        organization_id=org_id,
        user_id=user.id,
        detail=_json({"proposal_id": proposal_id, "version": ext.version_actual, "trigger": trigger}),
        commit=False,
    )
    return ver


def dashboard(db: Session, org_id: str) -> dict[str, Any]:
    proposals = db.query(CommercialProposal).filter(CommercialProposal.organization_id == org_id).all()
    by_estado: dict[str, int] = {}
    activas = 0
    valor_realizado = Decimal("0")
    valor_potencial = Decimal("0")
    for p in proposals:
        by_estado[p.estado] = by_estado.get(p.estado, 0) + 1
        if p.estado not in (ProposalStatus.RECHAZADA, ProposalStatus.VENCIDA, ProposalStatus.ACEPTADA):
            activas += 1
    values = motor_svc.sum_values_by_nature(db, org_id)
    opps = db.query(func.count(Opportunity.id)).filter(Opportunity.organization_id == org_id).scalar() or 0
    negociaciones_abiertas = (
        db.query(func.count(NegocioNegotiationEntry.id))
        .filter(NegocioNegotiationEntry.organization_id == org_id, NegocioNegotiationEntry.estado == "ABIERTA")
        .scalar()
        or 0
    )
    return {
        "organization_id": org_id,
        "oportunidades_total": opps,
        "propuestas_activas": activas,
        "propuestas_por_estado": by_estado,
        "negociaciones_abiertas": negociaciones_abiertas,
        "contrataciones": by_estado.get(ProposalStatus.ACEPTADA, 0),
        "valores": values,
        "nota_potencial": POTENCIAL_NOTE,
    }


def create_proposal_from_expediente(
    db: Session,
    user: User,
    org_id: str,
    *,
    evaluacion_id: str,
    opportunity_id: str | None = None,
    titulo: str | None = None,
    modelo_comercial: str | None = None,
) -> dict[str, Any]:
    from app.evaluacion_models import EvaluacionExpediente

    exp = (
        db.query(EvaluacionExpediente)
        .filter(EvaluacionExpediente.id == evaluacion_id, EvaluacionExpediente.organization_id == org_id)
        .first()
    )
    if not exp:
        raise HTTPException(status_code=404, detail="Expediente de evaluación no encontrado")
    if opportunity_id:
        com_svc._validate_opportunity(db, org_id, opportunity_id)
    else:
        from app.evaluacion_models import EvaluacionOportunidadLink

        link = (
            db.query(EvaluacionOportunidadLink)
            .filter(EvaluacionOportunidadLink.expediente_id == evaluacion_id)
            .first()
        )
        if link:
            opportunity_id = link.opportunity_id

    proposal = com_svc.create_proposal(
        db,
        org_id,
        {
            "titulo": titulo or f"Propuesta — {exp.titulo or exp.codigo}",
            "diagnostic_id": evaluacion_id,
        },
        user.id,
    )
    ext = _ensure_extension(db, proposal)
    ext.evaluacion_id = evaluacion_id
    ext.opportunity_id = opportunity_id
    ext.modelo_comercial = modelo_comercial or ModeloComercial.HIBRIDO
    ext.responsable_id = user.id
    ext.proximo_paso = "Completar valoración e importar componentes de valor"
    perspectives = _default_perspectives(proposal, ext)
    situacion = exp.necesidad or exp.objetivo or exp.titulo
    if situacion:
        perspectives[PerspectivaPropuesta.GERENCIA]["situacion"] = situacion
    ext.perspectivas_json = _json(perspectives)
    ext.documento_cliente_json = _json(_build_client_document(proposal, ext, perspectives))
    ext.documento_interno_json = _json(_build_internal_document(db, proposal, ext))
    trace = {"evaluacion_id": evaluacion_id, "opportunity_id": opportunity_id, "expediente_codigo": exp.codigo}
    proposal.traceability_json = _json(trace)
    if opportunity_id:
        try:
            com_svc.import_from_valuation(db, org_id, proposal.id, opportunity_id, user.id)
        except Exception:
            pass
    db.flush()
    write_audit(
        db,
        action="negocio.propuesta.desde_expediente",
        organization_id=org_id,
        user_id=user.id,
        detail=_json({"proposal_id": proposal.id, "evaluacion_id": evaluacion_id}),
        commit=False,
    )
    return get_proposal_negocio(db, org_id, proposal.id, include_internal=True)


def enrich_proposal_from_sources(db: Session, user: User, org_id: str, proposal_id: str) -> dict[str, Any]:
    proposal = com_svc._get_proposal(db, org_id, proposal_id)
    ext = _ensure_extension(db, proposal)
    if ext.opportunity_id:
        try:
            com_svc.import_from_valuation(db, org_id, proposal_id, ext.opportunity_id, user.id)
        except com_svc.CommercialValidationError:
            pass
    trace = _parse(proposal.traceability_json) or {}
    trace["enriched_at"] = _utcnow().isoformat()
    proposal.traceability_json = _json(trace)
    db.flush()
    return get_proposal_negocio(db, org_id, proposal_id, include_internal=True)


def apply_price_recommendation(
    db: Session,
    user: User,
    org_id: str,
    proposal_id: str,
    *,
    action: str,
    precio_decidido: float | None = None,
    justificacion: str | None = None,
) -> dict[str, Any]:
    proposal = com_svc._get_proposal(db, org_id, proposal_id)
    ext = _ensure_extension(db, proposal)
    rec: dict[str, Any] = {}
    try:
        rec = motor_svc.recommend_price(
            db,
            user,
            org_id,
            scope_type="ORGANIZACION",
            scope_id=proposal_id,
            persist=True,
        )
        ext.economic_recommendation_id = rec.get("id")
    except Exception:
        rec = {}
    precio_rec = rec.get("recommended_price")
    if action == PriceDecisionAction.ACEPTAR:
        if precio_rec is None:
            raise HTTPException(status_code=400, detail="Sin precio recomendado")
        if proposal.precio_sugerido is None and precio_rec is not None:
            proposal.precio_sugerido = Decimal(str(precio_rec))
        com_svc.set_final_price(db, org_id, proposal_id, float(precio_rec), justificacion or "Acepta recomendación motor económico", user.id)
        decided = precio_rec
    elif action == PriceDecisionAction.MODIFICAR:
        if precio_decidido is None:
            raise HTTPException(status_code=400, detail="precio_decidido requerido para MODIFICAR")
        if proposal.precio_sugerido is None:
            proposal.precio_sugerido = Decimal(str(precio_decidido))
            db.flush()
        com_svc.set_final_price(db, org_id, proposal_id, precio_decidido, justificacion, user.id)
        decided = precio_decidido
    elif action == PriceDecisionAction.DESCARTAR:
        decided = None
    else:
        raise HTTPException(status_code=400, detail="action inválida")
    dec = NegocioPriceDecision(
        proposal_id=proposal_id,
        organization_id=org_id,
        recommendation_id=rec.get("id"),
        action=action,
        precio_recomendado=precio_rec,
        precio_decidido=decided,
        justificacion=justificacion,
        user_id=user.id,
    )
    db.add(dec)
    if decided is not None:
        _record_price_phase(db, org_id, proposal_id, PricePhase.APROBADO, float(decided), user.id, nota=justificacion)
    if precio_rec is not None:
        _record_price_phase(db, org_id, proposal_id, PricePhase.RECOMENDADO, float(precio_rec), user.id, nota="Motor económico")
    db.flush()
    return {"decision": action, "precio_decidido": decided, "recommendation": rec, "auto_published": False}


def transition_proposal(db: Session, user: User, org_id: str, proposal_id: str, nuevo_estado: str, motivo: str | None = None) -> dict[str, Any]:
    if nuevo_estado not in ProposalStatus.ALL:
        raise HTTPException(status_code=400, detail="Estado no válido")
    proposal = com_svc._get_proposal(db, org_id, proposal_id)
    allowed = PROPOSAL_TRANSITIONS.get(proposal.estado, frozenset())
    if nuevo_estado not in allowed:
        raise HTTPException(status_code=422, detail=f"Transición no permitida: {proposal.estado} → {nuevo_estado}")
    if nuevo_estado == ProposalStatus.APROBADA:
        try:
            com_svc.approve_proposal(db, org_id, proposal_id, user.id)
        except com_svc.CommercialValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    elif nuevo_estado == ProposalStatus.EN_REVISION:
        ext = _ensure_extension(db, proposal)
        get_approval_adapter().ensure_records(db, org_id, proposal_id, ext.version_actual)
        proposal.estado = nuevo_estado
    elif nuevo_estado == ProposalStatus.ENVIADA:
        adapter = get_approval_adapter()
        can, missing = adapter.can_present(db, org_id, proposal_id, ext.version_actual if (ext := _ensure_extension(db, proposal)) else 1)
        if not can:
            write_audit(
                db,
                action="negocio.presentacion.rechazada",
                organization_id=org_id,
                user_id=user.id,
                detail=_json({"proposal_id": proposal_id, "niveles_pendientes": missing}),
                commit=False,
            )
            raise HTTPException(
                status_code=422,
                detail=f"Aprobaciones pendientes para presentar: {', '.join(missing)}",
            )
        if proposal.precio_final is None:
            raise HTTPException(status_code=422, detail="Debe aprobar precio antes de presentar")
        ext = _ensure_extension(db, proposal)
        ver = create_version_snapshot(db, user, org_id, proposal_id, trigger=ProposalVersionTrigger.PRESENTACION)
        precio_pres = float(proposal.precio_final)
        ver.precio_presentado = precio_pres
        ver.presented_by_id = user.id
        ext.precio_presentado = precio_pres
        _record_price_phase(
            db, org_id, proposal_id, PricePhase.PRESENTADO, precio_pres, user.id, version_number=ver.version_number
        )
        client_doc = _parse(ver.documento_cliente_json) or _build_client_document(
            proposal, ext, _parse(ext.perspectivas_json) or _default_perspectives(proposal, ext)
        )
        generate_and_store_pdf(
            db,
            user,
            org_id,
            proposal_id,
            ver,
            client_doc,
            prospecto=sync_svc.resolve_prospecto_name(db, ext),
            perspectivas=_parse(ext.perspectivas_json),
        )
        proposal.estado = ProposalStatus.ENVIADA
        sync_svc.sync_to_opportunity(db, org_id, proposal_id, actor_id=user.id)
    else:
        proposal.estado = nuevo_estado
    ext = _ensure_extension(db, proposal)
    if motivo:
        ext.proximo_paso = motivo
    if ext.opportunity_id and nuevo_estado == ProposalStatus.ENVIADA:
        opp = db.query(Opportunity).filter(Opportunity.id == ext.opportunity_id, Opportunity.organization_id == org_id).first()
        if opp and opp.estado in opp_svc.TRANSICIONES_PERMITIDAS.get(opp.estado, set()) | {opp.estado}:
            try:
                target = "PROPUESTA" if "PROPUESTA" in opp_svc.TRANSICIONES_PERMITIDAS.get(opp.estado, set()) else opp.estado
                if target != opp.estado:
                    opp_svc.transition_state(
                        db,
                        opp,
                        target,
                        actor_id=user.id,
                        motivo=motivo or "Propuesta presentada",
                    )
            except Exception:
                pass
    write_audit(
        db,
        action="negocio.propuesta.transicion",
        organization_id=org_id,
        user_id=user.id,
        detail=_json({"proposal_id": proposal_id, "estado": nuevo_estado}),
        commit=False,
    )
    db.flush()
    return get_proposal_negocio(db, org_id, proposal_id, include_internal=True)


def register_negotiation(
    db: Session,
    user: User,
    org_id: str,
    proposal_id: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    proposal = com_svc._get_proposal(db, org_id, proposal_id)
    ext = _ensure_extension(db, proposal)
    entry = NegocioNegotiationEntry(
        proposal_id=proposal_id,
        organization_id=org_id,
        version_presentada=data.get("version_presentada") or ext.version_actual,
        fecha_presentacion=data.get("fecha_presentacion") or _utcnow(),
        interlocutor=data.get("interlocutor"),
        observaciones=data.get("observaciones"),
        cambios_solicitados=data.get("cambios_solicitados"),
        proximo_paso=data.get("proximo_paso"),
        estado=data.get("estado", "ABIERTA"),
        created_by_id=user.id,
    )
    db.add(entry)
    if data.get("crear_nueva_version"):
        ver = create_version_snapshot(db, user, org_id, proposal_id, trigger=ProposalVersionTrigger.NEGOCIACION)
        entry.nueva_version_id = ver.id
        proposal.estado = ProposalStatus.BORRADOR
        get_approval_adapter().reset_for_version(db, org_id, proposal_id, ver.version_number)
        ext.proximo_paso = data.get("proximo_paso") or "Revisar cambios solicitados y completar aprobaciones"
    db.flush()
    return {"entry_id": entry.id, "proposal": get_proposal_negocio(db, org_id, proposal_id, include_internal=True)}


def convert_to_implementacion(db: Session, user: User, org_id: str, proposal_id: str, condiciones: str | None = None) -> dict[str, Any]:
    proposal = com_svc._get_proposal(db, org_id, proposal_id)
    ext = _ensure_extension(db, proposal)
    last_version = (
        db.query(NegocioProposalVersion)
        .filter(NegocioProposalVersion.proposal_id == proposal_id, NegocioProposalVersion.organization_id == org_id)
        .order_by(NegocioProposalVersion.version_number.desc())
        .first()
    )
    if proposal.estado != ProposalStatus.ACEPTADA:
        contracted = contract_proposal(db, user, org_id, proposal_id, condiciones=condiciones, version_id=last_version.id if last_version else None)
        contract_id = contracted["contract_id"]
        proposal = com_svc._get_proposal(db, org_id, proposal_id)
        contract = db.query(NegocioContractRecord).filter(NegocioContractRecord.id == contract_id).first()
    else:
        contract = cont_svc.ensure_contract_record(db, user, org_id, proposal_id, condiciones=condiciones)
        contract_id = contract.id if contract else None
    if ext.implementacion_proyecto_id:
        return {
            "proyecto_id": ext.implementacion_proyecto_id,
            "ya_existia": True,
            "contract_id": contract_id,
            "referencias": {
                "evaluacion_id": ext.evaluacion_id,
                "opportunity_id": ext.opportunity_id,
                "version_number": last_version.version_number if last_version else ext.version_actual,
                "document_id": last_version.pdf_document_id if last_version else None,
            },
        }
    proyecto = impl_svc.create_proyecto(
        db,
        org_id,
        {
            "titulo": proposal.titulo,
            "proposal_id": proposal.id,
            "alcance": None,
            "objetivos": ext.proximo_paso,
        },
        user.id,
    )
    if contract:
        cont_svc.enrich_proyecto_from_contrato(
            db, proyecto, proposal=proposal, ext=ext, contract=contract, version=last_version,
        )
    ext.implementacion_proyecto_id = proyecto.id
    ext.proximo_paso = "Levantamiento e implementación — datos transferidos desde propuesta"
    create_version_snapshot(db, user, org_id, proposal_id, trigger=ProposalVersionTrigger.CONTRATACION)
    write_audit(
        db,
        action="negocio.convertir.implementacion",
        organization_id=org_id,
        user_id=user.id,
        detail=_json({"proposal_id": proposal_id, "proyecto_id": proyecto.id}),
        commit=False,
    )
    db.flush()
    return {
        "proyecto_id": proyecto.id,
        "proposal_id": proposal_id,
        "contract_id": contract_id,
        "finops_budget_id": proyecto.finops_budget_id,
        "flujo": "PROSPECTO→DIAGNÓSTICO→PROPUESTA→NEGOCIACIÓN→CONTRATADO→LEVANTAMIENTO",
        "datos_reutilizados": bool(proyecto.compromiso_contractual_json),
        "referencias": {
            "evaluacion_id": ext.evaluacion_id,
            "opportunity_id": ext.opportunity_id,
            "version_number": last_version.version_number if last_version else ext.version_actual,
            "document_id": proyecto.documento_contrato_id or (last_version.pdf_document_id if last_version else None),
        },
        "compromiso": _parse(proyecto.compromiso_contractual_json),
    }


def get_proposal_negocio(
    db: Session,
    org_id: str,
    proposal_id: str,
    *,
    include_internal: bool = False,
) -> dict[str, Any]:
    detail = com_svc.proposal_to_detail(db, org_id, proposal_id)
    ext = db.query(NegocioProposalExtension).filter(NegocioProposalExtension.proposal_id == proposal_id).first()
    negocio = {}
    if ext:
        negocio = {
            "opportunity_id": ext.opportunity_id,
            "evaluacion_id": ext.evaluacion_id,
            "modelo_comercial": ext.modelo_comercial,
            "responsable_id": ext.responsable_id,
            "proximo_paso": ext.proximo_paso,
            "version_actual": ext.version_actual,
            "perspectivas": _parse(ext.perspectivas_json),
            "consumo_ia": _parse(ext.ia_consumo_json),
            "implementacion_proyecto_id": ext.implementacion_proyecto_id,
        }
        detail["documento_cliente"] = _parse(ext.documento_cliente_json)
        if include_internal:
            detail["documento_interno"] = _parse(ext.documento_interno_json)
            detail["economic_recommendation_id"] = ext.economic_recommendation_id
    else:
        detail["documento_cliente"] = None
    detail["negocio"] = negocio
    detail["nota_potencial"] = POTENCIAL_NOTE
    if not include_internal:
        for key in ("margen_pct", "costo_total", "precio_sugerido", "documento_interno", "economic_recommendation_id"):
            detail.pop(key, None)
    return detail


def update_ia_consumo(db: Session, org_id: str, proposal_id: str, data: dict[str, Any]) -> dict[str, Any]:
    proposal = com_svc._get_proposal(db, org_id, proposal_id)
    ext = _ensure_extension(db, proposal)
    payload = {
        "consumo_incluido_tokens": data.get("consumo_incluido_tokens"),
        "consumo_incluido_usd": data.get("consumo_incluido_usd"),
        "presupuesto_operacional": data.get("presupuesto_operacional"),
        "periodicidad": data.get("periodicidad"),
        "consumo_variable": data.get("consumo_variable", True),
        "proveedor": data.get("proveedor"),
        "modelo": data.get("modelo"),
        "credential_mode": data.get("credential_mode") or proposal.credential_mode,
        "infraestructura_licencias": data.get("infraestructura_licencias"),
        "excedente_overage": data.get("excedente_overage"),
        "nota": "No se ofrece IA ilimitada",
    }
    ext.ia_consumo_json = _json(payload)
    db.flush()
    return payload


def update_perspectives(
    db: Session,
    org_id: str,
    proposal_id: str,
    perspectiva: str,
    contenido: dict[str, Any],
) -> dict[str, Any]:
    proposal = com_svc._get_proposal(db, org_id, proposal_id)
    ext = _ensure_extension(db, proposal)
    if perspectiva not in PerspectivaPropuesta.ALL:
        raise HTTPException(status_code=400, detail="Perspectiva no válida")
    perspectives = _parse(ext.perspectivas_json) or _default_perspectives(proposal, ext)
    perspectives[perspectiva] = {**(perspectives.get(perspectiva) or {}), **contenido}
    ext.perspectivas_json = _json(perspectives)
    ext.documento_cliente_json = _json(_build_client_document(proposal, ext, perspectives))
    db.flush()
    return perspectives


def list_versions(db: Session, org_id: str, proposal_id: str) -> list[dict[str, Any]]:
    com_svc._get_proposal(db, org_id, proposal_id)
    rows = (
        db.query(NegocioProposalVersion)
        .filter(
            NegocioProposalVersion.proposal_id == proposal_id,
            NegocioProposalVersion.organization_id == org_id,
        )
        .order_by(NegocioProposalVersion.version_number.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "version_number": r.version_number,
            "trigger": r.trigger,
            "estado_comercial": r.estado_comercial,
            "estado_label": label_proposal_status(r.estado_comercial),
            "pdf_document_id": r.pdf_document_id,
            "precio_presentado": float(r.precio_presentado) if r.precio_presentado else None,
            "presented_by_id": r.presented_by_id,
            "approved_by_id": r.approved_by_id,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "documento_cliente": _parse(r.documento_cliente_json),
        }
        for r in rows
    ]


def list_negotiations(db: Session, org_id: str, proposal_id: str) -> list[dict[str, Any]]:
    com_svc._get_proposal(db, org_id, proposal_id)
    rows = (
        db.query(NegocioNegotiationEntry)
        .filter(
            NegocioNegotiationEntry.proposal_id == proposal_id,
            NegocioNegotiationEntry.organization_id == org_id,
        )
        .order_by(NegocioNegotiationEntry.created_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "version_presentada": r.version_presentada,
            "fecha_presentacion": r.fecha_presentacion.isoformat() if r.fecha_presentacion else None,
            "interlocutor": r.interlocutor,
            "observaciones": r.observaciones,
            "cambios_solicitados": r.cambios_solicitados,
            "estado": r.estado,
            "proximo_paso": r.proximo_paso,
            "nueva_version_id": r.nueva_version_id,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


def list_pipeline(db: Session, org_id: str, limit: int = 50) -> list[dict[str, Any]]:
    rows = (
        db.query(CommercialProposal)
        .filter(CommercialProposal.organization_id == org_id)
        .order_by(CommercialProposal.updated_at.desc())
        .limit(limit)
        .all()
    )
    out = []
    for p in rows:
        ext = db.query(NegocioProposalExtension).filter(NegocioProposalExtension.proposal_id == p.id).first()
        out.append(
            {
                "id": p.id,
                "codigo": p.codigo,
                "titulo": p.titulo,
                "estado": p.estado,
                "estado_label": label_proposal_status(p.estado),
                "valor_atribuible": float(p.valor_atribuible_total or 0) if p.valor_atribuible_total else None,
                "precio_final": float(p.precio_final or 0) if p.precio_final else None,
                "opportunity_id": ext.opportunity_id if ext else None,
                "evaluacion_id": ext.evaluacion_id if ext else None,
                "proximo_paso": ext.proximo_paso if ext else None,
                "version": ext.version_actual if ext else 1,
            }
        )
    return out


def approve_level(
    db: Session,
    user: User,
    org_id: str,
    proposal_id: str,
    nivel: str,
    *,
    comentario: str | None = None,
) -> dict[str, Any]:
    adapter = get_approval_adapter()
    ext = _ensure_extension(db, com_svc._get_proposal(db, org_id, proposal_id))
    row = adapter.approve(db, user, org_id, proposal_id, nivel, comentario=comentario, version_number=ext.version_actual)
    return {"nivel": row.nivel, "estado": row.estado, "aprobaciones": list_approval_status(db, org_id, proposal_id)}


def contract_proposal(
    db: Session,
    user: User,
    org_id: str,
    proposal_id: str,
    *,
    condiciones: str | None = None,
    version_id: str | None = None,
) -> dict[str, Any]:
    proposal = com_svc._get_proposal(db, org_id, proposal_id)
    ext = _ensure_extension(db, proposal)
    ver = None
    if version_id:
        ver = db.query(NegocioProposalVersion).filter(NegocioProposalVersion.id == version_id).first()
    if not ver:
        ver = (
            db.query(NegocioProposalVersion)
            .filter(NegocioProposalVersion.proposal_id == proposal_id)
            .order_by(NegocioProposalVersion.version_number.desc())
            .first()
        )
    if not ver or not ver.pdf_document_id:
        raise HTTPException(status_code=422, detail="Contratación requiere versión presentada con documento PDF")
    precio = float(proposal.precio_final or ext.precio_presentado or ver.precio_presentado or 0)
    contract = NegocioContractRecord(
        proposal_id=proposal_id,
        organization_id=org_id,
        version_id=ver.id,
        version_number=ver.version_number,
        document_id=ver.pdf_document_id,
        precio_contratado=precio,
        modelo_comercial=ext.modelo_comercial,
        condiciones=condiciones,
        responsable_id=user.id,
        proximo_paso="Convertir en implementación",
        created_by_id=user.id,
    )
    db.add(contract)
    ext.precio_contratado = precio
    _record_price_phase(db, org_id, proposal_id, PricePhase.CONTRATADO, precio, user.id, version_number=ver.version_number)
    budget = cont_finops.ensure_operational_budget_from_contract(
        db, org_id=org_id, contract=contract, ext=ext, proposal=proposal,
    )
    if proposal.estado != ProposalStatus.ACEPTADA:
        proposal.estado = ProposalStatus.ACEPTADA
    write_audit(
        db,
        action="negocio.contratacion",
        organization_id=org_id,
        user_id=user.id,
        detail=_json({"proposal_id": proposal_id, "version": ver.version_number, "precio": precio}),
        commit=False,
    )
    db.flush()
    return {
        "contract_id": contract.id,
        "version_number": ver.version_number,
        "precio_contratado": precio,
        "finops_budget_id": budget.id if budget else contract.finops_budget_id,
    }


def get_proposal_detail(db: Session, org_id: str, proposal_id: str, *, include_internal: bool = False) -> dict[str, Any]:
    detail = get_proposal_negocio(db, org_id, proposal_id, include_internal=include_internal)
    ext = db.query(NegocioProposalExtension).filter(NegocioProposalExtension.proposal_id == proposal_id).first()
    detail["estado_label"] = label_proposal_status(detail.get("estado"))
    detail["aprobaciones"] = list_approval_status(db, org_id, proposal_id, ext.version_actual if ext else 1)
    detail["versiones"] = list_versions(db, org_id, proposal_id)
    detail["negociaciones"] = list_negotiations(db, org_id, proposal_id)
    detail["fases_precio"] = list_price_phases(db, org_id, proposal_id)
    detail["sync_log"] = sync_svc.get_sync_log(db, org_id, proposal_id)
    detail["prospecto"] = sync_svc.resolve_prospecto_name(db, ext)
    if ext:
        detail["negocio"]["precio_presentado"] = float(ext.precio_presentado) if ext.precio_presentado else None
        detail["negocio"]["precio_contratado"] = float(ext.precio_contratado) if ext.precio_contratado else None
        detail["negocio"]["sync_revision"] = ext.sync_revision
    return detail


def list_price_phases(db: Session, org_id: str, proposal_id: str) -> list[dict[str, Any]]:
    rows = (
        db.query(NegocioPricePhaseRecord)
        .filter(NegocioPricePhaseRecord.proposal_id == proposal_id, NegocioPricePhaseRecord.organization_id == org_id)
        .order_by(NegocioPricePhaseRecord.created_at.asc())
        .all()
    )
    from app.negocio_labels import PRICE_PHASE_LABELS

    return [
        {
            "fase": r.fase,
            "fase_label": PRICE_PHASE_LABELS.get(r.fase, r.fase),
            "monto": float(r.monto) if r.monto else None,
            "version_number": r.version_number,
            "nota": r.nota,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


def get_document_pdf(db: Session, org_id: str, document_id: str) -> tuple[bytes, str, str]:
    doc = (
        db.query(NegocioProposalDocument)
        .filter(NegocioProposalDocument.id == document_id, NegocioProposalDocument.organization_id == org_id)
        .first()
    )
    if not doc or not doc.content_bytes:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return doc.content_bytes, doc.filename, doc.content_type


def generate_proposal_pdf(
    db: Session,
    user: User,
    org_id: str,
    proposal_id: str,
    *,
    version_number: int | None = None,
) -> dict[str, Any]:
    proposal = com_svc._get_proposal(db, org_id, proposal_id)
    ext = _ensure_extension(db, proposal)
    ver = None
    if version_number:
        ver = (
            db.query(NegocioProposalVersion)
            .filter(
                NegocioProposalVersion.proposal_id == proposal_id,
                NegocioProposalVersion.version_number == version_number,
            )
            .first()
        )
    if not ver:
        ver = create_version_snapshot(db, user, org_id, proposal_id, trigger=ProposalVersionTrigger.REVISION_INTERNA)
    client_doc = _parse(ver.documento_cliente_json) or _build_client_document(
        proposal, ext, _parse(ext.perspectivas_json) or _default_perspectives(proposal, ext)
    )
    doc = generate_and_store_pdf(
        db,
        user,
        org_id,
        proposal_id,
        ver,
        client_doc,
        prospecto=sync_svc.resolve_prospecto_name(db, ext),
        perspectivas=_parse(ext.perspectivas_json),
    )
    return {"document_id": doc.id, "filename": doc.filename, "version_number": ver.version_number, "sha256": doc.content_sha256}


def sync_opportunity(db: Session, org_id: str, proposal_id: str, direction: str = "both") -> dict[str, Any]:
    result: dict[str, Any] = {}
    if direction in ("from", "both"):
        result["from_opportunity"] = sync_svc.sync_from_opportunity(db, org_id, proposal_id)
    if direction in ("to", "both"):
        result["to_opportunity"] = sync_svc.sync_to_opportunity(db, org_id, proposal_id)
    return result
