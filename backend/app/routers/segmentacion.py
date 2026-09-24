"""Router — Segmentación y planes verticales (1310)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import check_permission
from app.schemas_segmentation import (
    CustomPackageRequest,
    DiscountRequest,
    PackageCompareRequest,
    PackageCreate,
    PackagePriceRequest,
    ProfileUpsert,
    ScalingRequest,
    SectorCreate,
    SegmentCreate,
)
from app.services import segmentation_service as svc

router = APIRouter(prefix="/api/segmentacion", tags=["segmentacion"])


def _handle_validation(exc: svc.SegmentationValidationError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.get("/sectores")
def list_sectors(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "segmentacion.view", db)
    return [svc._sector_to_dict(s) for s in svc.list_sectors(db, user.organization_id)]


@router.post("/sectores", status_code=status.HTTP_201_CREATED)
def create_sector(body: SectorCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "segmentacion.manage", db)
    org_id = body.organization_id or user.organization_id
    row = svc.create_sector(db, org_id, body.model_dump(), user.id)
    db.commit()
    return svc._sector_to_dict(row)


@router.get("/segmentos")
def list_segments(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "segmentacion.view", db)
    return [svc._segment_to_dict(s) for s in svc.list_segments(db, user.organization_id)]


@router.post("/segmentos", status_code=status.HTTP_201_CREATED)
def create_segment(body: SegmentCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "segmentacion.manage", db)
    org_id = body.organization_id or user.organization_id
    row = svc.create_segment(db, org_id, body.model_dump(), user.id)
    db.commit()
    return svc._segment_to_dict(row)


@router.get("/perfil")
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "segmentacion.view", db)
    row = svc.get_profile(db, user.organization_id)
    return svc._profile_to_dict(row) if row else None


@router.put("/perfil")
def upsert_profile(body: ProfileUpsert, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "segmentacion.manage", db)
    row = svc.upsert_profile(db, user.organization_id, body.model_dump(exclude_none=True), user.id)
    db.commit()
    return svc._profile_to_dict(row)


@router.get("/paquetes")
def list_packages(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "planes.view", db)
    return [svc._package_to_dict(p) for p in svc.list_packages(db, user.organization_id)]


@router.get("/paquetes/{package_id}")
def get_package(package_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "planes.view", db)
    return svc._package_to_dict(svc.get_package(db, user.organization_id, package_id))


@router.post("/paquetes", status_code=status.HTTP_201_CREATED)
def create_package(body: PackageCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "planes.manage", db)
    org_id = body.organization_id or user.organization_id
    row = svc.create_package(db, org_id, body.model_dump(), user.id)
    db.commit()
    return svc._package_to_dict(row)


@router.post("/paquetes/{package_id}/activar")
def activate_package(package_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "planes.manage", db)
    pkg = svc.get_package(db, user.organization_id, package_id)
    pkg.lifecycle_status = "ACTIVO"
    db.commit()
    return {"id": pkg.id, "lifecycle_status": pkg.lifecycle_status}


@router.post("/paquetes/{package_id}/versionar")
def version_package(package_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "planes.manage", db)
    snap = svc.version_package(db, user.organization_id, package_id, user.id)
    db.commit()
    return {"id": snap.id, "version_number": snap.version_number}


@router.post("/paquetes/personalizado", status_code=status.HTTP_201_CREATED)
def create_custom_package(body: CustomPackageRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "planes.manage", db)
    row = svc.create_custom_package(db, user.organization_id, body.base_package_id, body.overrides, user.id)
    db.commit()
    return svc._package_to_dict(row)


@router.post("/comparar")
def compare_packages(body: PackageCompareRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "planes.view", db)
    try:
        return svc.compare_packages(db, user.organization_id, body.package_ids)
    except svc.SegmentationValidationError as exc:
        raise _handle_validation(exc) from exc


@router.get("/recomendar")
def recommend_plan(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "planes.recommend", db)
    try:
        result = svc.recommend_plan(db, user.organization_id)
        db.commit()
        return result
    except svc.SegmentationValidationError as exc:
        db.rollback()
        raise _handle_validation(exc) from exc


@router.post("/escalamiento")
def suggest_scaling(body: ScalingRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "planes.recommend", db)
    try:
        return svc.suggest_scaling(db, user.organization_id, body.model_dump(exclude_none=True))
    except svc.SegmentationValidationError as exc:
        raise _handle_validation(exc) from exc


@router.post("/descuentos")
def apply_discount(body: DiscountRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "planes.approve_discount", db)
    result = svc.apply_discount(db, user.organization_id, body.model_dump(), user.id)
    db.commit()
    return result


@router.post("/paquetes/{package_id}/precio")
def price_package(package_id: str, body: PackagePriceRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "planes.view", db)
    return svc.price_with_package(db, user.organization_id, package_id, body.valor_atribuible, body.costo_total)


@router.post("/planes/{plan_id}/versionar")
def version_plan(plan_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "planes.manage", db)
    snap = svc.version_plan(db, user.organization_id, plan_id, user.id)
    db.commit()
    return {"id": snap.id, "version_number": snap.version_number}
