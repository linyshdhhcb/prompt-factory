from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Depends, Query
from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import ModelConfig as ModelConfigORM, Prompt
from app.models.schemas import (
    HealthResponse,
    ModelConfigResponse,
    PromptResponse,
)
from app.services.dedup import generate_embedding
from app.services.llm_provider import get_provider

logger = logging.getLogger(__name__)

_start_time: float = time.monotonic()

router = APIRouter(prefix="/api/v1", tags=["history"])


@router.get("/history/{project_id}")
async def get_history(
    project_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    count_stmt = select(func.count()).select_from(Prompt).where(Prompt.project_id == project_id)
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = (
        select(Prompt)
        .where(Prompt.project_id == project_id)
        .order_by(Prompt.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    prompts = list(result.scalars().all())

    return {
        "project_id": project_id,
        "total": total,
        "limit": limit,
        "offset": offset,
        "prompts": [PromptResponse.model_validate(p) for p in prompts],
    }


@router.delete("/project/{project_id}")
async def delete_project_prompts(project_id: str, db: AsyncSession = Depends(get_db)):
    count_stmt = select(func.count()).select_from(Prompt).where(Prompt.project_id == project_id)
    count = (await db.execute(count_stmt)).scalar() or 0

    await db.execute(delete(Prompt).where(Prompt.project_id == project_id))
    await db.flush()

    logger.info("Deleted %d prompts for project %s", count, project_id)
    return {"project_id": project_id, "deleted_count": count}


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    status_value = "healthy"
    db_status = "connected"
    model_statuses: dict[str, str] = {}
    embedding_status = "available"

    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error("DB health check failed: %s", exc)
        status_value = "unhealthy"
        db_status = "disconnected"

    if status_value != "unhealthy":
        try:
            stmt = select(ModelConfigORM).where(ModelConfigORM.enabled.is_(True))
            result = await db.execute(stmt)
            models = list(result.scalars().all())

            unavailable_count = 0
            for model in models:
                try:
                    schema = ModelConfigResponse.model_validate(model)
                    provider = get_provider(schema)
                    available = await provider.health_check()
                    model_statuses[model.name] = "available" if available else "unavailable"
                    if not available:
                        unavailable_count += 1
                except Exception as exc:
                    model_statuses[model.name] = "error"
                    unavailable_count += 1

            if unavailable_count > 0 and unavailable_count == len(models):
                status_value = "unhealthy"
            elif unavailable_count > 0:
                status_value = "degraded"
        except Exception as exc:
            logger.error("Model health check failed: %s", exc)
            status_value = "degraded"

    if status_value != "unhealthy":
        try:
            embedding = await generate_embedding("health check")
            if embedding is None:
                embedding_status = "unavailable"
                if status_value == "healthy":
                    status_value = "degraded"
        except Exception as exc:
            logger.error("Embedding health check failed: %s", exc)
            embedding_status = "unavailable"
            if status_value == "healthy":
                status_value = "degraded"

    return HealthResponse(
        status=status_value,
        version="0.1.0",
        database=db_status,
        models=model_statuses,
        embedding=embedding_status,
    )
