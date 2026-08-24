"""Cálculo de próximas ejecuciones con timezone (CURSOR-810)."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from app.enums import ScheduleType


def _to_utc(dt: datetime, tz_name: str) -> datetime:
    tz = ZoneInfo(tz_name)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    return dt.astimezone(timezone.utc)


def _local_now(tz_name: str) -> datetime:
    return datetime.now(ZoneInfo(tz_name))


def parse_recurrence(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    return json.loads(raw)


def occurrence_key(scheduled_for: datetime) -> str:
    return scheduled_for.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def compute_next_run(
    *,
    schedule_type: str | None,
    tz_name: str,
    start_at: datetime | None,
    end_at: datetime | None,
    recurrence_config: dict[str, Any] | None,
    after: datetime | None = None,
    last_run_at: datetime | None = None,
) -> datetime | None:
    if not schedule_type:
        return None

    now_utc = after or datetime.now(timezone.utc)
    cfg = recurrence_config or {}
    hour = int(cfg.get("hour", 9))
    minute = int(cfg.get("minute", 0))

    if schedule_type == ScheduleType.ONE_TIME:
        if not start_at:
            return None
        target = _to_utc(start_at, tz_name)
        if target <= now_utc:
            return None
        if end_at and target > _to_utc(end_at, tz_name):
            return None
        return target

    local = _local_now(tz_name)
    candidate_local = local.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if schedule_type == ScheduleType.INTERVAL:
        interval = int(cfg.get("interval_minutes") or 60)
        base = last_run_at or start_at or now_utc
        if base.tzinfo is None:
            base = base.replace(tzinfo=timezone.utc)
        nxt = base + timedelta(minutes=interval)
        if nxt <= now_utc:
            nxt = now_utc + timedelta(minutes=interval)
        return _apply_end(nxt, end_at, tz_name)

    if candidate_local <= local:
        candidate_local += timedelta(days=1)

    if schedule_type == ScheduleType.DAILY:
        nxt = _to_utc(candidate_local, tz_name)
        while nxt <= now_utc:
            candidate_local += timedelta(days=1)
            nxt = _to_utc(candidate_local, tz_name)
        return _apply_end(nxt, end_at, tz_name)

    if schedule_type == ScheduleType.WEEKLY:
        weekdays = cfg.get("weekdays") or [0]
        for _ in range(370):
            if candidate_local.weekday() in weekdays:
                nxt = _to_utc(candidate_local, tz_name)
                if nxt > now_utc:
                    return _apply_end(nxt, end_at, tz_name)
            candidate_local += timedelta(days=1)
        return None

    if schedule_type == ScheduleType.MONTHLY:
        dom = int(cfg.get("day_of_month") or 1)
        candidate_local = candidate_local.replace(day=min(dom, 28))
        for _ in range(24):
            try:
                candidate_local = candidate_local.replace(day=dom)
            except ValueError:
                candidate_local = candidate_local.replace(day=28)
            nxt = _to_utc(candidate_local, tz_name)
            if nxt > now_utc:
                return _apply_end(nxt, end_at, tz_name)
            if candidate_local.month == 12:
                candidate_local = candidate_local.replace(year=candidate_local.year + 1, month=1)
            else:
                candidate_local = candidate_local.replace(month=candidate_local.month + 1)
        return None

    return None


def _apply_end(nxt: datetime, end_at: datetime | None, tz_name: str) -> datetime | None:
    if end_at and nxt > _to_utc(end_at, tz_name):
        return None
    return nxt
