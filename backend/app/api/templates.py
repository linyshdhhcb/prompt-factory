from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AppException
from app.models import MetaPromptTemplate
from app.models.schemas import (
    MetaTemplateCreate,
    MetaTemplateResponse,
    MetaTemplateUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/meta-templates", tags=["templates"])


@router.get("")
async def list_templates(
    scope: Optional[str] = Query(default=None),
    project_id: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(MetaPromptTemplate)
    count_stmt = select(func.count()).select_from(MetaPromptTemplate)

    if scope is not None:
        stmt = stmt.where(MetaPromptTemplate.scope == scope)
        count_stmt = count_stmt.where(MetaPromptTemplate.scope == scope)
    if project_id is not None:
        stmt = stmt.where(MetaPromptTemplate.project_id == project_id)
        count_stmt = count_stmt.where(MetaPromptTemplate.project_id == project_id)

    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.order_by(MetaPromptTemplate.id.asc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    templates = list(result.scalars().all())

    return {
        "items": [MetaTemplateResponse.model_validate(t) for t in templates],
        "total": total,
    }


@router.post("", response_model=MetaTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(body: MetaTemplateCreate, db: AsyncSession = Depends(get_db)):
    template = MetaPromptTemplate(
        template=body.template,
        scope=body.scope,
        project_id=body.project_id,
        enabled=body.enabled,
        weight=body.weight,
    )
    db.add(template)
    await db.flush()
    await db.refresh(template)
    logger.info("Created meta-template id=%d scope=%s", template.id, template.scope)
    return MetaTemplateResponse.model_validate(template)


@router.put("/{id}", response_model=MetaTemplateResponse)
async def update_template(
    id: int,
    body: MetaTemplateUpdate,
    db: AsyncSession = Depends(get_db),
):
    template = await db.get(MetaPromptTemplate, id)
    if template is None:
        raise AppException(
            code="TEMPLATE_NOT_FOUND",
            message=f"Meta-template {id} not found",
            status_code=404,
            detail={"id": id},
        )

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(template, key, value)

    await db.flush()
    await db.refresh(template)
    logger.info("Updated meta-template id=%d", id)
    return MetaTemplateResponse.model_validate(template)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(id: int, db: AsyncSession = Depends(get_db)):
    template = await db.get(MetaPromptTemplate, id)
    if template is None:
        raise AppException(
            code="TEMPLATE_NOT_FOUND",
            message=f"Meta-template {id} not found",
            status_code=404,
            detail={"id": id},
        )
    await db.delete(template)
    await db.flush()
    logger.info("Deleted meta-template id=%d", id)
