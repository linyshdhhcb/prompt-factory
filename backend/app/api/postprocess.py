from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AppException
from app.models import PostprocessRule
from app.models.schemas import (
    PostprocessRuleCreate,
    PostprocessRuleResponse,
    PostprocessRuleUpdate,
    SortOrderRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/postprocess", tags=["postprocess"])


@router.get("/rules")
async def list_rules(
    scope: Optional[str] = Query(default=None),
    project_id: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(PostprocessRule)
    count_stmt = select(func.count()).select_from(PostprocessRule)

    if scope is not None:
        stmt = stmt.where(PostprocessRule.scope == scope)
        count_stmt = count_stmt.where(PostprocessRule.scope == scope)
    if project_id is not None:
        stmt = stmt.where(PostprocessRule.project_id == project_id)
        count_stmt = count_stmt.where(PostprocessRule.project_id == project_id)

    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.order_by(PostprocessRule.sort_order, PostprocessRule.id.asc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    rules = list(result.scalars().all())

    return {
        "items": [PostprocessRuleResponse.model_validate(r) for r in rules],
        "total": total,
    }


@router.post("/rules", response_model=PostprocessRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(body: PostprocessRuleCreate, db: AsyncSession = Depends(get_db)):
    rule = PostprocessRule(
        name=body.name,
        description=body.description,
        probability=body.probability,
        params=body.params,
        scope=body.scope,
        project_id=body.project_id,
        enabled=body.enabled,
        sort_order=body.sort_order,
    )
    db.add(rule)
    await db.flush()
    await db.refresh(rule)
    logger.info("Created postprocess rule id=%d name=%s", rule.id, rule.name)
    return PostprocessRuleResponse.model_validate(rule)


@router.put("/rules/{id}", response_model=PostprocessRuleResponse)
async def update_rule(
    id: int,
    body: PostprocessRuleUpdate,
    db: AsyncSession = Depends(get_db),
):
    rule = await db.get(PostprocessRule, id)
    if rule is None:
        raise AppException(
            code="RULE_NOT_FOUND",
            message=f"Postprocess rule {id} not found",
            status_code=404,
            detail={"id": id},
        )

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)

    await db.flush()
    await db.refresh(rule)
    logger.info("Updated postprocess rule id=%d", id)
    return PostprocessRuleResponse.model_validate(rule)


@router.delete("/rules/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(id: int, db: AsyncSession = Depends(get_db)):
    rule = await db.get(PostprocessRule, id)
    if rule is None:
        raise AppException(
            code="RULE_NOT_FOUND",
            message=f"Postprocess rule {id} not found",
            status_code=404,
            detail={"id": id},
        )
    await db.delete(rule)
    await db.flush()
    logger.info("Deleted postprocess rule id=%d", id)


@router.put("/rules/sort", status_code=status.HTTP_204_NO_CONTENT)
async def update_sort_order(body: SortOrderRequest, db: AsyncSession = Depends(get_db)):
    for item in body.items:
        rule = await db.get(PostprocessRule, item.id)
        if rule is not None:
            rule.sort_order = item.sort_order
    await db.flush()
    logger.info("Updated sort order for %d rules", len(body.items))
