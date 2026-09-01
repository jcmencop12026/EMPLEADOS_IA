"""Servicio de inteligencia de resultados — orquesta indicadores, informes y línea base."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.baseline_models import LineaBase, LineaBaseImpacto, LineaBaseMedicion
from app.evaluacion_models import EvaluacionExpediente, EvaluacionHallazgo
from app.resultados_models import (
    ResultadoDimensionNodo,
    ResultadoEvidencia,
    ResultadoIndicador,
    ResultadoInformeImpacto,
    ResultadoPlanAccion,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _num(v: float | Decimal | None) -> float | None:
    if v is None:
        return None
    return float(v)


def _indicador_dict(ind: ResultadoIndicador) -> dict[str, Any]:
    tiene_real = ind.valor_real is not None
    return {
        "id": ind.id,
        "organization_id": ind.organization_id,
        "nombre": ind.nombre,
        "definicion": ind.definicion,
        "unidad": ind.unidad,
        "fuente": ind.fuente,
        "dimension_json": json.loads(ind.dimension_json) if ind.dimension_json else None,
        "periodo": ind.periodo,
        "antes": _num(ind.valor_antes),
        "proyectado": _num(ind.valor_proyectado),
        "real": _num(ind.valor_real),
        "meta": _num(ind.meta),
        "fecha_medicion": ind.fecha_medicion.isoformat() if ind.fecha_medicion else None,
        "evidencia_ref": ind.evidencia_ref,
        "confianza": ind.confianza,
        "calidad": ind.calidad,
        "tipo_analitica": ind.tipo_analitica,
        "responsable_id": ind.responsable_id,
        "correlation_id": ind.correlation_id,
        "expediente_id": ind.expediente_id,
        "hallazgo_id": ind.hallazgo_id,
        "opportunity_id": ind.opportunity_id,
        "linea_base_id": ind.linea_base_id,
        "proceso": ind.proceso,
        "visible_entidad": ind.visible_entidad,
        "tiene_medicion_real": tiene_real,
        "sin_medicion_posterior": ind.valor_proyectado is not None and not tiene_real,
        "created_at": ind.created_at.isoformat() if ind.created_at else None,
    }


def create_indicador(
    db: Session,
    organization_id: str,
    *,
    nombre: str,
    unidad: str = "unidad",
    definicion: str | None = None,
    fuente: str = "MANUAL",
    valor_antes: float | None = None,
    valor_proyectado: float | None = None,
    valor_real: float | None = None,
    meta: float | None = None,
    expediente_id: str | None = None,
    hallazgo_id: str | None = None,
    opportunity_id: str | None = None,
    linea_base_id: str | None = None,
    proceso: str | None = None,
    periodo: str | None = None,
    tipo_analitica: str = "DESCRIPTIVA",
    evidencia_ref: str | None = None,
    confianza: str = "MEDIA",
    visible_entidad: bool = False,
    correlation_id: str | None = None,
    responsable_id: str | None = None,
    dimension: dict | None = None,
) -> dict[str, Any]:
    ind = ResultadoIndicador(
        organization_id=organization_id,
        nombre=nombre,
        definicion=definicion,
        unidad=unidad,
        fuente=fuente,
        valor_antes=valor_antes,
        valor_proyectado=valor_proyectado,
        valor_real=valor_real,
        meta=meta,
        expediente_id=expediente_id,
        hallazgo_id=hallazgo_id,
        opportunity_id=opportunity_id,
        linea_base_id=linea_base_id,
        proceso=proceso,
        periodo=periodo,
        tipo_analitica=tipo_analitica,
        evidencia_ref=evidencia_ref,
        confianza=confianza,
        visible_entidad=visible_entidad,
        correlation_id=correlation_id or str(uuid.uuid4()),
        responsable_id=responsable_id,
        dimension_json=json.dumps(dimension) if dimension else None,
        fecha_medicion=_utcnow() if valor_real is not None else None,
    )
    db.add(ind)
    db.commit()
    db.refresh(ind)
    return _indicador_dict(ind)


def sync_indicador_from_linea_base(db: Session, linea_base_id: str, organization_id: str) -> dict[str, Any]:
    """Puente a Bloque 1200 — no duplica motor de línea base."""
    lb = db.query(LineaBase).filter(LineaBase.id == linea_base_id, LineaBase.organization_id == organization_id).first()
    if not lb:
        raise ValueError("Línea base no encontrada")
    impacto = (
        db.query(LineaBaseImpacto)
        .filter(LineaBaseImpacto.linea_base_id == lb.id, LineaBaseImpacto.organization_id == organization_id)
        .order_by(desc(LineaBaseImpacto.created_at))
        .first()
    )
    valor_real = float(impacto.impacto_real) if impacto and impacto.impacto_real is not None else None
    if valor_real is None and impacto:
        valor_real = float(impacto.valor_posterior) if impacto.valor_posterior is not None else None
    existing = (
        db.query(ResultadoIndicador)
        .filter(ResultadoIndicador.linea_base_id == lb.id, ResultadoIndicador.organization_id == organization_id)
        .first()
    )
    if existing:
        existing.valor_antes = float(lb.valor_base)
        existing.valor_proyectado = float(lb.impacto_esperado) if lb.impacto_esperado is not None else existing.valor_proyectado
        if valor_real is not None:
            existing.valor_real = valor_real
            existing.fecha_medicion = _utcnow()
        existing.fuente = lb.fuente
        db.commit()
        db.refresh(existing)
        return _indicador_dict(existing)
    return create_indicador(
        db,
        organization_id,
        nombre=lb.indicador,
        definicion=lb.descripcion,
        unidad=lb.unidad,
        fuente=lb.fuente,
        valor_antes=float(lb.valor_base),
        valor_proyectado=float(lb.impacto_esperado) if lb.impacto_esperado is not None else None,
        valor_real=valor_real,
        linea_base_id=lb.id,
        opportunity_id=lb.opportunity_id,
        proceso=lb.proceso,
        tipo_analitica="COMPARATIVA",
        evidencia_ref=lb.evidencia_json,
    )


def list_indicadores(
    db: Session,
    organization_id: str,
    *,
    expediente_id: str | None = None,
    periodo: str | None = None,
    proceso: str | None = None,
    tipo_analitica: str | None = None,
    q: str | None = None,
    solo_con_real: bool = False,
    visible_entidad: bool | None = None,
) -> list[dict[str, Any]]:
    qry = db.query(ResultadoIndicador).filter(ResultadoIndicador.organization_id == organization_id)
    if expediente_id:
        qry = qry.filter(ResultadoIndicador.expediente_id == expediente_id)
    if periodo:
        qry = qry.filter(ResultadoIndicador.periodo == periodo)
    if proceso:
        qry = qry.filter(ResultadoIndicador.proceso == proceso)
    if tipo_analitica:
        qry = qry.filter(ResultadoIndicador.tipo_analitica == tipo_analitica)
    if solo_con_real:
        qry = qry.filter(ResultadoIndicador.valor_real.isnot(None))
    if visible_entidad is not None:
        qry = qry.filter(ResultadoIndicador.visible_entidad == visible_entidad)
    rows = qry.order_by(desc(ResultadoIndicador.updated_at)).all()
    if q:
        ql = q.lower()
        rows = [r for r in rows if ql in r.nombre.lower() or (r.definicion and ql in r.definicion.lower())]
    return [_indicador_dict(r) for r in rows]


def register_medicion_real(
    db: Session,
    indicador_id: str,
    organization_id: str,
    *,
    valor_real: float,
    evidencia_ref: str | None = None,
    calidad: str = "VALIDADA",
) -> dict[str, Any]:
    ind = (
        db.query(ResultadoIndicador)
        .filter(ResultadoIndicador.id == indicador_id, ResultadoIndicador.organization_id == organization_id)
        .first()
    )
    if not ind:
        raise ValueError("Indicador no encontrado")
    ind.valor_real = valor_real
    ind.fecha_medicion = _utcnow()
    ind.evidencia_ref = evidencia_ref or ind.evidencia_ref
    ind.calidad = calidad
    db.commit()
    db.refresh(ind)
    return _indicador_dict(ind)


def get_drill_down(db: Session, indicador_id: str, organization_id: str) -> dict[str, Any]:
    ind = (
        db.query(ResultadoIndicador)
        .filter(ResultadoIndicador.id == indicador_id, ResultadoIndicador.organization_id == organization_id)
        .first()
    )
    if not ind:
        raise ValueError("Indicador no encontrado")
    nodos = (
        db.query(ResultadoDimensionNodo)
        .filter(ResultadoDimensionNodo.indicador_id == indicador_id, ResultadoDimensionNodo.organization_id == organization_id)
        .order_by(ResultadoDimensionNodo.nivel, ResultadoDimensionNodo.etiqueta)
        .all()
    )
    return {
        "indicador": _indicador_dict(ind),
        "nodos": [
            {
                "id": n.id,
                "parent_id": n.parent_id,
                "nivel": n.nivel,
                "codigo": n.codigo,
                "etiqueta": n.etiqueta,
                "valor": float(n.valor) if n.valor is not None else None,
                "unidad": n.unidad,
                "metadata": json.loads(n.metadata_json) if n.metadata_json else None,
            }
            for n in nodos
        ],
    }


def add_dimension_nodo(
    db: Session,
    organization_id: str,
    indicador_id: str,
    *,
    codigo: str,
    etiqueta: str,
    valor: float | None = None,
    unidad: str | None = None,
    parent_id: str | None = None,
    nivel: int = 0,
    metadata: dict | None = None,
) -> dict[str, Any]:
    nodo = ResultadoDimensionNodo(
        organization_id=organization_id,
        indicador_id=indicador_id,
        parent_id=parent_id,
        nivel=nivel,
        codigo=codigo,
        etiqueta=etiqueta,
        valor=valor,
        unidad=unidad,
        metadata_json=json.dumps(metadata) if metadata else None,
    )
    db.add(nodo)
    db.commit()
    db.refresh(nodo)
    return {"id": nodo.id, "codigo": nodo.codigo, "etiqueta": nodo.etiqueta, "valor": float(nodo.valor) if nodo.valor else None}


def build_antes_proyectado_real(
    db: Session,
    organization_id: str,
    *,
    expediente_id: str | None = None,
) -> dict[str, Any]:
    """Capa semántica unificada ANTES / PROYECTADO / REAL."""
    indicadores = list_indicadores(db, organization_id, expediente_id=expediente_id)
    filas = []
    for ind in indicadores:
        filas.append({
            "id": ind["id"],
            "nombre": ind["nombre"],
            "unidad": ind["unidad"],
            "antes": ind["antes"],
            "proyectado": ind["proyectado"],
            "real": ind["real"],
            "meta": ind["meta"],
            "proyectado_es_inferencia": ind["proyectado"] is not None and ind["tipo_analitica"] in ("PREDICTIVA", "PRESCRIPTIVA", "DIAGNOSTICA"),
            "sin_medicion_posterior": ind["sin_medicion_posterior"],
            "evidencia_ref": ind["evidencia_ref"],
            "confianza": ind["confianza"],
            "fuente": ind["fuente"],
            "tipo_analitica": ind["tipo_analitica"],
            "visible_entidad": ind.get("visible_entidad", False),
            "periodo": ind.get("periodo"),
        })
    return {
        "organization_id": organization_id,
        "expediente_id": expediente_id,
        "indicadores": filas,
        "nota": "PROYECTADO no equivale a resultado conseguido. REAL requiere evidencia registrada.",
    }


def _build_narrativa(contenido: dict[str, Any]) -> str:
    """Informe narrativo determinístico — sin depender de IA generativa."""
    secciones = []
    secciones.append(f"## Qué ocurrió\n{contenido.get('que_ocurrio', '—')}")
    secciones.append(f"## Por qué ocurrió\n{contenido.get('por_que', '—')}")
    secciones.append(f"## Quién o qué intervino\n{contenido.get('quien', '—')}")
    secciones.append(f"## Cómo se actuó\n{contenido.get('como', '—')}")
    secciones.append(f"## Cuándo\n{contenido.get('cuando', '—')}")
    secciones.append(f"## Cuánto impactó\n{contenido.get('cuanto', '—')}")
    secciones.append(f"## Qué hicimos\n{contenido.get('que_hicimos', '—')}")
    secciones.append(f"## Qué cambió o mejoró\n{contenido.get('que_mejoro', '—')}")
    secciones.append(f"## Qué sigue\n{contenido.get('que_sigue', '—')}")
    if contenido.get("advertencia_proyectado"):
        secciones.append(f"\n> **Nota:** {contenido['advertencia_proyectado']}")
    return "\n\n".join(secciones)


def generate_informe_impacto(
    db: Session,
    organization_id: str,
    user_id: str,
    *,
    expediente_id: str,
    tipo: str = "IMPACTO",
    visibilidad: str = "INTERNO",
) -> dict[str, Any]:
    exp = (
        db.query(EvaluacionExpediente)
        .filter(EvaluacionExpediente.id == expediente_id, EvaluacionExpediente.organization_id == organization_id)
        .first()
    )
    if not exp:
        raise ValueError("Expediente no encontrado")
    hallazgos = (
        db.query(EvaluacionHallazgo)
        .filter(EvaluacionHallazgo.expediente_id == expediente_id, EvaluacionHallazgo.organization_id == organization_id)
        .all()
    )
    apr = build_antes_proyectado_real(db, organization_id, expediente_id=expediente_id)
    planes = (
        db.query(ResultadoPlanAccion)
        .filter(ResultadoPlanAccion.expediente_id == expediente_id, ResultadoPlanAccion.organization_id == organization_id)
        .all()
    )
    evidencias = (
        db.query(ResultadoEvidencia)
        .join(ResultadoIndicador, ResultadoIndicador.id == ResultadoEvidencia.indicador_id)
        .filter(ResultadoIndicador.expediente_id == expediente_id, ResultadoIndicador.organization_id == organization_id)
        .all()
    )

    hallazgo_titulos = ", ".join(h.titulo for h in hallazgos[:5]) or "Sin hallazgos registrados"
    indicadores_con_real = [i for i in apr["indicadores"] if i["real"] is not None]
    indicadores_sin_real = [i for i in apr["indicadores"] if i["proyectado"] is not None and i["real"] is None]

    cuanto_lines = []
    for i in apr["indicadores"]:
        line = f"- **{i['nombre']}** ({i['unidad']}): ANTES {i['antes']}, PROYECTADO {i['proyectado']}, REAL {i['real'] if i['real'] is not None else 'sin medición posterior'}"
        cuanto_lines.append(line)

    contenido = {
        "que_ocurrio": f"Evaluación {exp.codigo} — {exp.titulo} para {exp.entidad_nombre}. Hallazgos: {hallazgo_titulos}.",
        "por_que": exp.necesidad or "Causa raíz documentada en expediente.",
        "quien": f"Entidad: {exp.entidad_nombre}. Área/proceso: {exp.area_proceso or '—'}.",
        "como": f"Nivel {exp.nivel}. Información completada al {exp.porcentaje_informacion}%.",
        "cuando": f"Expediente creado {exp.created_at.date().isoformat() if exp.created_at else '—'}.",
        "cuanto": "\n".join(cuanto_lines) if cuanto_lines else "Sin indicadores cuantificados.",
        "que_hicimos": "; ".join(p.accion for p in planes) or "Acciones en plan de mejoramiento pendientes de registro.",
        "que_mejoro": (
            f"{len(indicadores_con_real)} indicador(es) con medición REAL registrada."
            if indicadores_con_real
            else "Aún no hay mediciones REAL posteriores."
        ),
        "que_sigue": (
            f"Seguimiento de {len(indicadores_sin_real)} proyección(es) sin medición REAL."
            if indicadores_sin_real
            else "Consolidar evidencia y cerrar acciones pendientes."
        ),
        "advertencia_proyectado": (
            "Los valores PROYECTADO son expectativas o inferencias; no deben interpretarse como resultados conseguidos."
            if indicadores_sin_real
            else None
        ),
        "indicadores": apr["indicadores"],
        "hallazgos_count": len(hallazgos),
        "acciones_count": len(planes),
        "evidencias_count": len(evidencias),
        "correlation_id": exp.correlation_id,
    }

    last_ver = (
        db.query(ResultadoInformeImpacto)
        .filter(
            ResultadoInformeImpacto.expediente_id == expediente_id,
            ResultadoInformeImpacto.organization_id == organization_id,
        )
        .order_by(desc(ResultadoInformeImpacto.version))
        .first()
    )
    version = (last_ver.version + 1) if last_ver else 1
    narrativa = _build_narrativa(contenido)
    informe = ResultadoInformeImpacto(
        organization_id=organization_id,
        expediente_id=expediente_id,
        tipo=tipo,
        version=version,
        titulo=f"Informe de impacto — {exp.codigo} v{version}",
        visibilidad=visibilidad,
        estado="GENERADO",
        contenido_json=json.dumps(contenido, ensure_ascii=False, default=str),
        narrativa=narrativa,
        correlation_id=exp.correlation_id,
        created_by=user_id,
    )
    db.add(informe)
    db.commit()
    db.refresh(informe)
    try:
        from app.events.bus import EventMessage, publish

        publish(
            EventMessage(
                event_type="RESULTADOS_INFORME_GENERADO",
                organization_id=organization_id,
                correlation_id=exp.correlation_id,
                payload={
                    "informe_id": informe.id,
                    "informe_titulo": informe.titulo,
                    "informe_version": informe.version,
                    "expediente_id": expediente_id,
                    "expediente_codigo": exp.codigo,
                    "responsable_id": user_id,
                    "visibilidad": visibilidad,
                },
            ),
            db,
        )
        db.commit()
    except Exception:
        pass
    return informe_dict(informe)


def informe_dict(inf: ResultadoInformeImpacto) -> dict[str, Any]:
    return {
        "id": inf.id,
        "organization_id": inf.organization_id,
        "expediente_id": inf.expediente_id,
        "opportunity_id": inf.opportunity_id,
        "tipo": inf.tipo,
        "version": inf.version,
        "titulo": inf.titulo,
        "visibilidad": inf.visibilidad,
        "estado": inf.estado,
        "contenido": json.loads(inf.contenido_json),
        "narrativa": inf.narrativa,
        "correlation_id": inf.correlation_id,
        "created_by": inf.created_by,
        "created_at": inf.created_at.isoformat() if inf.created_at else None,
    }


def list_informes(db: Session, organization_id: str, *, expediente_id: str | None = None) -> list[dict[str, Any]]:
    qry = db.query(ResultadoInformeImpacto).filter(ResultadoInformeImpacto.organization_id == organization_id)
    if expediente_id:
        qry = qry.filter(ResultadoInformeImpacto.expediente_id == expediente_id)
    return [informe_dict(i) for i in qry.order_by(desc(ResultadoInformeImpacto.created_at)).all()]


def get_informe(db: Session, informe_id: str, organization_id: str) -> dict[str, Any]:
    inf = (
        db.query(ResultadoInformeImpacto)
        .filter(ResultadoInformeImpacto.id == informe_id, ResultadoInformeImpacto.organization_id == organization_id)
        .first()
    )
    if not inf:
        raise ValueError("Informe no encontrado")
    return informe_dict(inf)


def create_plan_accion(
    db: Session,
    organization_id: str,
    *,
    expediente_id: str,
    accion: str,
    hallazgo_id: str | None = None,
    causa: str | None = None,
    indicador_id: str | None = None,
    responsable_id: str | None = None,
    fecha_meta: datetime | None = None,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    plan = ResultadoPlanAccion(
        organization_id=organization_id,
        expediente_id=expediente_id,
        hallazgo_id=hallazgo_id,
        indicador_id=indicador_id,
        causa=causa,
        accion=accion,
        responsable_id=responsable_id,
        fecha_meta=fecha_meta,
        correlation_id=correlation_id,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return _plan_dict(plan)


def _plan_dict(p: ResultadoPlanAccion) -> dict[str, Any]:
    return {
        "id": p.id,
        "expediente_id": p.expediente_id,
        "hallazgo_id": p.hallazgo_id,
        "indicador_id": p.indicador_id,
        "causa": p.causa,
        "accion": p.accion,
        "responsable_id": p.responsable_id,
        "fecha_meta": p.fecha_meta.isoformat() if p.fecha_meta else None,
        "estado": p.estado,
        "evidencia_ref": p.evidencia_ref,
        "resultado": p.resultado,
        "seguimiento_notas": p.seguimiento_notas,
        "correlation_id": p.correlation_id,
    }


def list_planes(db: Session, organization_id: str, *, expediente_id: str | None = None) -> list[dict[str, Any]]:
    qry = db.query(ResultadoPlanAccion).filter(ResultadoPlanAccion.organization_id == organization_id)
    if expediente_id:
        qry = qry.filter(ResultadoPlanAccion.expediente_id == expediente_id)
    return [_plan_dict(p) for p in qry.order_by(desc(ResultadoPlanAccion.created_at)).all()]


def update_plan_accion(
    db: Session,
    plan_id: str,
    organization_id: str,
    *,
    estado: str | None = None,
    resultado: str | None = None,
    evidencia_ref: str | None = None,
    seguimiento_notas: str | None = None,
) -> dict[str, Any]:
    plan = (
        db.query(ResultadoPlanAccion)
        .filter(ResultadoPlanAccion.id == plan_id, ResultadoPlanAccion.organization_id == organization_id)
        .first()
    )
    if not plan:
        raise ValueError("Plan no encontrado")
    if estado:
        plan.estado = estado
    if resultado is not None:
        plan.resultado = resultado
    if evidencia_ref is not None:
        plan.evidencia_ref = evidencia_ref
    if seguimiento_notas is not None:
        plan.seguimiento_notas = seguimiento_notas
    db.commit()
    db.refresh(plan)
    return _plan_dict(plan)


def get_trazabilidad_resultados(db: Session, organization_id: str, *, expediente_id: str) -> dict[str, Any]:
    exp = (
        db.query(EvaluacionExpediente)
        .filter(EvaluacionExpediente.id == expediente_id, EvaluacionExpediente.organization_id == organization_id)
        .first()
    )
    if not exp:
        raise ValueError("Expediente no encontrado")
    indicadores = list_indicadores(db, organization_id, expediente_id=expediente_id)
    informes = list_informes(db, organization_id, expediente_id=expediente_id)
    planes = list_planes(db, organization_id, expediente_id=expediente_id)
    return {
        "expediente_id": expediente_id,
        "correlation_id": exp.correlation_id,
        "cadena": [
            {"tipo": "expediente", "id": exp.id, "codigo": exp.codigo},
            *[{"tipo": "indicador", "id": i["id"], "nombre": i["nombre"], "fuente": i["fuente"]} for i in indicadores],
            *[{"tipo": "informe", "id": inf["id"], "version": inf["version"]} for inf in informes],
            *[{"tipo": "accion", "id": p["id"], "estado": p["estado"]} for p in planes],
        ],
        "indicadores": indicadores,
        "informes": informes,
        "planes": planes,
    }


def add_evidencia(
    db: Session,
    organization_id: str,
    user_id: str,
    *,
    titulo: str,
    indicador_id: str | None = None,
    informe_id: str | None = None,
    descripcion: str | None = None,
    fuente: str = "MANUAL",
    referencia: str | None = None,
) -> dict[str, Any]:
    ev = ResultadoEvidencia(
        organization_id=organization_id,
        indicador_id=indicador_id,
        informe_id=informe_id,
        titulo=titulo,
        descripcion=descripcion,
        fuente=fuente,
        referencia=referencia,
        created_by=user_id,
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return {"id": ev.id, "titulo": ev.titulo, "referencia": ev.referencia, "fuente": ev.fuente}
