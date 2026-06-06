from __future__ import annotations

import asyncio

from fastapi import HTTPException

from app.db.session import get_session_factory
from app.services.settings import SettingService

AUDIT_LOG_PRUNE_INTERVAL_SECONDS = 24 * 60 * 60


async def audit_log_prune_loop() -> None:
    while True:
        await asyncio.sleep(AUDIT_LOG_PRUNE_INTERVAL_SECONDS)
        await asyncio.to_thread(prune_audit_logs_once)


def prune_audit_logs_once() -> None:
    try:
        with get_session_factory()() as db:
            SettingService(db).prune_audit_logs()
            db.commit()
    except HTTPException as exc:
        if exc.status_code != 503:
            raise
