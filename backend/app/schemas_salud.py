"""Esquemas API del motor IPS (SALUD-960)."""

from typing import Any

from pydantic import BaseModel, Field


class DatasetUploadRequest(BaseModel):
    ips_name: str
    source_type: str
    filename: str | None = None
    profile_code: str | None = None
    records: list[dict[str, Any]]


class AnalysisRequest(BaseModel):
    ips_name: str
    request_text: str = "Analiza la situación financiera y operativa de esta IPS."
    dataset_ids: list[str] | None = None
    inline_datasets: dict[str, list[dict[str, Any]]] | None = None


class ActionPlanRequest(BaseModel):
    propuesta_ids: list[str]


class FeedbackRequest(BaseModel):
    target_type: str
    target_id: str
    feedback_type: str
    comment: str | None = None


class ActionResultRequest(BaseModel):
    meta: str | None = None
    resultado: str | None = None
    outcome: str = "NO_EVALUADO"


class QuestionRequest(BaseModel):
    pregunta: str


class SpecialistSelectionRequest(BaseModel):
    request_text: str
    available_data: list[str] | None = None
