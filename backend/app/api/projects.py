from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ProjectNotFoundError
from app.core.snowflake import snowflake_id
from app.models import (
    MetaPromptTemplate,
    ModelConfig,
    PersonaTrait,
    PostprocessRule,
    Project,
    Prompt,
)
from app.models.schemas import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


@router.get("", response_model=ProjectListResponse)
async def list_projects(db: AsyncSession = Depends(get_db)):
    count_stmt = select(func.count()).select_from(Project)
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = select(Project).order_by(Project.created_at.desc())
    result = await db.execute(stmt)
    projects = list(result.scalars().all())

    return ProjectListResponse(
        items=[ProjectResponse.model_validate(p) for p in projects],
        total=total,
    )


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(body: ProjectCreate, db: AsyncSession = Depends(get_db)):
    project_id = body.id if body.id else snowflake_id()
    project = Project(
        id=project_id,
        name=body.name,
        description=body.description,
        config=body.config,
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)
    logger.info("Created project id=%s name=%s", project.id, project.name)
    return ProjectResponse.model_validate(project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if project is None:
        raise ProjectNotFoundError(project_id)
    return ProjectResponse.model_validate(project)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    body: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if project is None:
        raise ProjectNotFoundError(project_id)

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)

    await db.flush()
    await db.refresh(project)
    logger.info("Updated project id=%s fields=%s", project_id, list(update_data.keys()))
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if project is None:
        raise ProjectNotFoundError(project_id)

    await db.execute(delete(Prompt).where(Prompt.project_id == project_id))
    await db.execute(delete(PersonaTrait).where(PersonaTrait.project_id == project_id))
    await db.execute(delete(MetaPromptTemplate).where(MetaPromptTemplate.project_id == project_id))
    await db.execute(delete(PostprocessRule).where(PostprocessRule.project_id == project_id))
    await db.execute(delete(ModelConfig).where(ModelConfig.project_id == project_id))
    await db.delete(project)
    await db.flush()
    logger.info("Deleted project id=%s and all related data", project_id)
