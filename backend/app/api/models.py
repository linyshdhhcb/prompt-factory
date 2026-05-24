from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import decrypt_api_key, encrypt_api_key, mask_api_key
from app.core.database import get_db
from app.core.exceptions import AppException
from app.models import ModelConfig as ModelConfigORM
from app.models.schemas import (
    ModelConfigCreate,
    ModelConfigResponse,
    ModelConfigUpdate,
)
from app.services.llm_provider import get_provider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/models", tags=["models"])


def _build_response(model: ModelConfigORM) -> ModelConfigResponse:
    api_key_encrypted = getattr(model, "api_key_encrypted", None)

    if api_key_encrypted:
        plain = decrypt_api_key(api_key_encrypted)
        masked = mask_api_key(plain)
    else:
        masked = "****"

    resp = ModelConfigResponse.model_validate(model)
    resp.api_key_masked = masked
    return resp


@router.get("")
async def list_models(
    scope: Optional[str] = Query(default=None),
    project_id: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ModelConfigORM)
    count_stmt = select(func.count()).select_from(ModelConfigORM)

    if scope is not None:
        stmt = stmt.where(ModelConfigORM.scope == scope)
        count_stmt = count_stmt.where(ModelConfigORM.scope == scope)
    if project_id is not None:
        stmt = stmt.where(ModelConfigORM.project_id == project_id)
        count_stmt = count_stmt.where(ModelConfigORM.project_id == project_id)

    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.order_by(ModelConfigORM.id.asc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    models = list(result.scalars().all())

    return {
        "items": [_build_response(m) for m in models],
        "total": total,
    }


@router.post("", response_model=ModelConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_model(body: ModelConfigCreate, db: AsyncSession = Depends(get_db)):
    api_key_encrypted = encrypt_api_key(body.api_key) if body.api_key else None

    model = ModelConfigORM(
        name=body.name,
        provider_type=body.provider_type,
        api_key_encrypted=api_key_encrypted,
        base_url=body.base_url,
        model_name=body.model_name,
        weight=body.weight,
        max_tokens=body.max_tokens,
        timeout=body.timeout,
        scope=body.scope,
        project_id=body.project_id,
        enabled=body.enabled,
    )
    db.add(model)
    await db.flush()
    await db.refresh(model)
    logger.info("Created model config id=%d name=%s", model.id, model.name)
    return _build_response(model)


@router.put("/{id}", response_model=ModelConfigResponse)
async def update_model(
    id: int,
    body: ModelConfigUpdate,
    db: AsyncSession = Depends(get_db),
):
    model = await db.get(ModelConfigORM, id)
    if model is None:
        raise AppException(
            code="MODEL_CONFIG_NOT_FOUND",
            message=f"Model config {id} not found",
            status_code=404,
            detail={"id": id},
        )

    update_data = body.model_dump(exclude_unset=True)

    if "api_key" in update_data:
        raw_key = update_data.pop("api_key")
        if raw_key:
            model.api_key_encrypted = encrypt_api_key(raw_key)
        else:
            model.api_key_encrypted = None

    for key, value in update_data.items():
        setattr(model, key, value)

    await db.flush()
    await db.refresh(model)
    logger.info("Updated model config id=%d", id)
    return _build_response(model)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(id: int, db: AsyncSession = Depends(get_db)):
    model = await db.get(ModelConfigORM, id)
    if model is None:
        raise AppException(
            code="MODEL_CONFIG_NOT_FOUND",
            message=f"Model config {id} not found",
            status_code=404,
            detail={"id": id},
        )
    await db.delete(model)
    await db.flush()
    logger.info("Deleted model config id=%d", id)


@router.post("/{id}/test")
async def test_model(id: int, db: AsyncSession = Depends(get_db)):
    model = await db.get(ModelConfigORM, id)
    if model is None:
        raise AppException(
            code="MODEL_CONFIG_NOT_FOUND",
            message=f"Model config {id} not found",
            status_code=404,
            detail={"id": id},
        )

    from app.services.llm_provider import _orm_to_schema
    schema = _orm_to_schema(model)
    provider = get_provider(schema)
    available = await provider.health_check()
    logger.info("Model connectivity test id=%d name=%s available=%s", id, model.name, available)
    return {"available": available}
