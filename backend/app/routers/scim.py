"""Router SCIM 2.0 — RFC 7643/7644 (1380)."""

from __future__ import annotations

import time
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.scim_auth_service import authenticate_scim_token, check_scim_rate_limit
from app.services.scim_audit import record_scim_metric
from app.services.scim_filter import ScimFilterError, parse_filter
from app.services.scim_group_service import (
    create_group,
    delete_group,
    get_group,
    list_groups,
    patch_group,
    update_group,
)
from app.services.scim_response import (
    RESOURCE_TYPES,
    SCHEMAS,
    SERVICE_PROVIDER_CONFIG,
    list_response,
    scim_error,
)
from app.services.scim_user_service import ScimUserError, create_user, delete_user, get_user, list_users, patch_user, update_user

router = APIRouter(prefix="/scim/v2", tags=["scim"])


def _base_url(request: Request) -> str:
    return str(request.base_url).rstrip("/")


def _get_scim_context(request: Request, db: Session = Depends(get_db)):
    auth = request.headers.get("Authorization", "")
    if not auth.lower().startswith("bearer "):
        return scim_error(401, "Autenticación Bearer requerida"), None, None
    token_plain = auth.split(" ", 1)[1].strip()
    try:
        token_row = authenticate_scim_token(db, token_plain)
        check_scim_rate_limit(db, organization_id=token_row.organization_id, token_id=token_row.id)
    except ValueError as exc:
        if str(exc) == "RATE_LIMIT":
            return scim_error(429, "Demasiadas solicitudes SCIM"), None, None
        return scim_error(401, "Token SCIM inválido o expirado"), None, None
    return None, token_row, db


@router.get("/ServiceProviderConfig")
def service_provider_config(request: Request, db: Session = Depends(get_db)):
    err, token_row, _ = _get_scim_context(request, db)
    if err:
        return err
    record_scim_metric(db, token_row.organization_id, requests_delta=1)
    db.commit()
    return SERVICE_PROVIDER_CONFIG


@router.get("/ResourceTypes")
def resource_types(request: Request, db: Session = Depends(get_db)):
    err, token_row, _ = _get_scim_context(request, db)
    if err:
        return err
    record_scim_metric(db, token_row.organization_id, requests_delta=1)
    db.commit()
    return RESOURCE_TYPES


@router.get("/Schemas")
def schemas(request: Request, db: Session = Depends(get_db)):
    err, token_row, _ = _get_scim_context(request, db)
    if err:
        return err
    record_scim_metric(db, token_row.organization_id, requests_delta=1)
    db.commit()
    return SCHEMAS


@router.get("/Users")
def scim_list_users(
    request: Request,
    filter: str | None = None,
    startIndex: int = 1,
    count: int = 100,
    db: Session = Depends(get_db),
):
    start = time.monotonic()
    err, token_row, _ = _get_scim_context(request, db)
    if err:
        return err
    try:
        filters = parse_filter(filter)
    except ScimFilterError as exc:
        return scim_error(400, str(exc), scim_type="invalidFilter")
    resources, total = list_users(
        db, token_row.organization_id, base_url=_base_url(request),
        start_index=startIndex, count=min(count, 200), filters=filters,
    )
    record_scim_metric(db, token_row.organization_id, requests_delta=1, latency_ms=int((time.monotonic() - start) * 1000))
    db.commit()
    return list_response(resources, total=total, start=startIndex, count=len(resources))


@router.post("/Users", status_code=201)
async def scim_create_user(request: Request, db: Session = Depends(get_db)):
    start = time.monotonic()
    err, token_row, _ = _get_scim_context(request, db)
    if err:
        return err
    payload = await request.json()
    idem = request.headers.get("X-Idempotency-Key") or request.headers.get("Idempotency-Key")
    try:
        result = create_user(
            db, token_row.organization_id, payload, base_url=_base_url(request),
            token_id=token_row.id, idempotency_key=idem,
        )
        record_scim_metric(db, token_row.organization_id, requests_delta=1, latency_ms=int((time.monotonic() - start) * 1000))
        db.commit()
        return JSONResponse(status_code=201, content=result)
    except ScimUserError as exc:
        record_scim_metric(db, token_row.organization_id, requests_delta=1, errors_delta=1)
        db.commit()
        return scim_error(exc.status, str(exc), scim_type=exc.scim_type)


@router.get("/Users/{user_id}")
def scim_get_user(user_id: str, request: Request, db: Session = Depends(get_db)):
    err, token_row, _ = _get_scim_context(request, db)
    if err:
        return err
    try:
        result = get_user(db, token_row.organization_id, user_id, base_url=_base_url(request))
        record_scim_metric(db, token_row.organization_id, requests_delta=1)
        db.commit()
        return result
    except ScimUserError as exc:
        record_scim_metric(db, token_row.organization_id, errors_delta=1)
        db.commit()
        return scim_error(exc.status, str(exc), scim_type=exc.scim_type)


@router.put("/Users/{user_id}")
async def scim_put_user(user_id: str, request: Request, db: Session = Depends(get_db)):
    err, token_row, _ = _get_scim_context(request, db)
    if err:
        return err
    payload = await request.json()
    try:
        result = update_user(db, token_row.organization_id, user_id, payload, base_url=_base_url(request), token_id=token_row.id)
        record_scim_metric(db, token_row.organization_id, requests_delta=1)
        db.commit()
        return result
    except ScimUserError as exc:
        record_scim_metric(db, token_row.organization_id, errors_delta=1)
        db.commit()
        return scim_error(exc.status, str(exc), scim_type=exc.scim_type)


@router.patch("/Users/{user_id}")
async def scim_patch_user(user_id: str, request: Request, db: Session = Depends(get_db)):
    err, token_row, _ = _get_scim_context(request, db)
    if err:
        return err
    payload = await request.json()
    ops = payload.get("Operations") or []
    try:
        result = patch_user(db, token_row.organization_id, user_id, ops, base_url=_base_url(request), token_id=token_row.id)
        record_scim_metric(db, token_row.organization_id, requests_delta=1)
        db.commit()
        return result
    except ScimUserError as exc:
        record_scim_metric(db, token_row.organization_id, errors_delta=1)
        db.commit()
        return scim_error(exc.status, str(exc), scim_type=exc.scim_type)


@router.delete("/Users/{user_id}", status_code=204)
def scim_delete_user(user_id: str, request: Request, db: Session = Depends(get_db)):
    err, token_row, _ = _get_scim_context(request, db)
    if err:
        return err
    try:
        delete_user(db, token_row.organization_id, user_id, token_id=token_row.id)
        record_scim_metric(db, token_row.organization_id, requests_delta=1)
        db.commit()
        return JSONResponse(status_code=204, content=None)
    except ScimUserError as exc:
        record_scim_metric(db, token_row.organization_id, errors_delta=1)
        db.commit()
        return scim_error(exc.status, str(exc), scim_type=exc.scim_type)


@router.get("/Groups")
def scim_list_groups(
    request: Request,
    filter: str | None = None,
    startIndex: int = 1,
    count: int = 100,
    db: Session = Depends(get_db),
):
    err, token_row, _ = _get_scim_context(request, db)
    if err:
        return err
    try:
        filters = parse_filter(filter)
    except ScimFilterError as exc:
        return scim_error(400, str(exc), scim_type="invalidFilter")
    resources, total = list_groups(
        db, token_row.organization_id, base_url=_base_url(request),
        start_index=startIndex, count=min(count, 200), filters=filters,
    )
    record_scim_metric(db, token_row.organization_id, requests_delta=1)
    db.commit()
    return list_response(resources, total=total, start=startIndex, count=len(resources))


@router.post("/Groups", status_code=201)
async def scim_create_group(request: Request, db: Session = Depends(get_db)):
    err, token_row, _ = _get_scim_context(request, db)
    if err:
        return err
    payload = await request.json()
    try:
        result = create_group(db, token_row.organization_id, payload, base_url=_base_url(request), token_id=token_row.id)
        record_scim_metric(db, token_row.organization_id, requests_delta=1)
        db.commit()
        return JSONResponse(status_code=201, content=result)
    except ScimUserError as exc:
        record_scim_metric(db, token_row.organization_id, errors_delta=1)
        db.commit()
        return scim_error(exc.status, str(exc), scim_type=exc.scim_type)


@router.get("/Groups/{group_id}")
def scim_get_group(group_id: str, request: Request, db: Session = Depends(get_db)):
    err, token_row, _ = _get_scim_context(request, db)
    if err:
        return err
    try:
        result = get_group(db, token_row.organization_id, group_id, base_url=_base_url(request))
        record_scim_metric(db, token_row.organization_id, requests_delta=1)
        db.commit()
        return result
    except ScimUserError as exc:
        return scim_error(exc.status, str(exc), scim_type=exc.scim_type)


@router.put("/Groups/{group_id}")
async def scim_put_group(group_id: str, request: Request, db: Session = Depends(get_db)):
    err, token_row, _ = _get_scim_context(request, db)
    if err:
        return err
    payload = await request.json()
    try:
        result = update_group(db, token_row.organization_id, group_id, payload, base_url=_base_url(request), token_id=token_row.id)
        record_scim_metric(db, token_row.organization_id, requests_delta=1)
        db.commit()
        return result
    except ScimUserError as exc:
        return scim_error(exc.status, str(exc), scim_type=exc.scim_type)


@router.patch("/Groups/{group_id}")
async def scim_patch_group(group_id: str, request: Request, db: Session = Depends(get_db)):
    err, token_row, _ = _get_scim_context(request, db)
    if err:
        return err
    payload = await request.json()
    try:
        result = patch_group(db, token_row.organization_id, group_id, payload.get("Operations") or [], base_url=_base_url(request), token_id=token_row.id)
        record_scim_metric(db, token_row.organization_id, requests_delta=1)
        db.commit()
        return result
    except ScimUserError as exc:
        return scim_error(exc.status, str(exc), scim_type=exc.scim_type)


@router.delete("/Groups/{group_id}", status_code=204)
def scim_delete_group(group_id: str, request: Request, db: Session = Depends(get_db)):
    err, token_row, _ = _get_scim_context(request, db)
    if err:
        return err
    try:
        delete_group(db, token_row.organization_id, group_id, token_id=token_row.id)
        record_scim_metric(db, token_row.organization_id, requests_delta=1)
        db.commit()
        return JSONResponse(status_code=204, content=None)
    except ScimUserError as exc:
        return scim_error(exc.status, str(exc), scim_type=exc.scim_type)
