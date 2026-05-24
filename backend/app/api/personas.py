from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AppException
from app.models import PersonaTrait
from app.models.schemas import (
    PersonaTraitCreate,
    PersonaTraitListResponse,
    PersonaTraitResponse,
    PersonaTraitUpdate,
)
from app.services.persona import get_merged_traits

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/persona", tags=["personas"])


@router.get("/traits", response_model=PersonaTraitListResponse)
async def list_traits(
    scope: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    project_id: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(PersonaTrait)
    count_stmt = select(func.count()).select_from(PersonaTrait)

    if scope is not None:
        stmt = stmt.where(PersonaTrait.scope == scope)
        count_stmt = count_stmt.where(PersonaTrait.scope == scope)
    if category is not None:
        stmt = stmt.where(PersonaTrait.category == category)
        count_stmt = count_stmt.where(PersonaTrait.category == category)
    if project_id is not None:
        stmt = stmt.where(PersonaTrait.project_id == project_id)
        count_stmt = count_stmt.where(PersonaTrait.project_id == project_id)

    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.order_by(PersonaTrait.category, PersonaTrait.id.asc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    traits = list(result.scalars().all())

    return PersonaTraitListResponse(
        items=[PersonaTraitResponse.model_validate(t) for t in traits],
        total=total,
    )


@router.post("/traits", response_model=PersonaTraitResponse, status_code=status.HTTP_201_CREATED)
async def create_trait(body: PersonaTraitCreate, db: AsyncSession = Depends(get_db)):
    trait = PersonaTrait(
        category=body.category,
        label=body.label,
        traits=body.traits,
        weight=body.weight,
        scope=body.scope,
        project_id=body.project_id,
    )
    db.add(trait)
    await db.flush()
    await db.refresh(trait)
    logger.info("Created persona trait id=%d category=%s", trait.id, trait.category)
    return PersonaTraitResponse.model_validate(trait)


@router.put("/traits/{id}", response_model=PersonaTraitResponse)
async def update_trait(id: int, body: PersonaTraitUpdate, db: AsyncSession = Depends(get_db)):
    trait = await db.get(PersonaTrait, id)
    if trait is None:
        raise AppException(
            code="TRAIT_NOT_FOUND",
            message=f"Persona trait {id} not found",
            status_code=404,
            detail={"id": id},
        )

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(trait, key, value)

    await db.flush()
    await db.refresh(trait)
    logger.info("Updated persona trait id=%d", id)
    return PersonaTraitResponse.model_validate(trait)


@router.delete("/traits/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trait(id: int, db: AsyncSession = Depends(get_db)):
    trait = await db.get(PersonaTrait, id)
    if trait is None:
        raise AppException(
            code="TRAIT_NOT_FOUND",
            message=f"Persona trait {id} not found",
            status_code=404,
            detail={"id": id},
        )
    await db.delete(trait)
    await db.flush()
    logger.info("Deleted persona trait id=%d", id)


@router.post("/traits/import", response_model=PersonaTraitListResponse, status_code=status.HTTP_201_CREATED)
async def import_traits(body: list[PersonaTraitCreate], db: AsyncSession = Depends(get_db)):
    traits = []
    for item in body:
        trait = PersonaTrait(
            category=item.category,
            label=item.label,
            traits=item.traits,
            weight=item.weight,
            scope=item.scope,
            project_id=item.project_id,
        )
        db.add(trait)
        traits.append(trait)

    await db.flush()
    for t in traits:
        await db.refresh(t)

    logger.info("Imported %d persona traits", len(traits))
    return PersonaTraitListResponse(
        items=[PersonaTraitResponse.model_validate(t) for t in traits],
        total=len(traits),
    )


@router.get("/preview/{project_id}", response_model=PersonaTraitListResponse)
async def preview_persona(project_id: str, db: AsyncSession = Depends(get_db)):
    merged = await get_merged_traits(project_id, db)
    return PersonaTraitListResponse(
        items=[PersonaTraitResponse.model_validate(t) for t in merged],
        total=len(merged),
    )
