from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import async_session_factory, get_db
from app.core.exceptions import AppException, ModelUnavailableError, ProjectNotFoundError
from app.models import PostprocessRule, Project
from app.models.schemas import (
    GenerateAsyncResponse,
    GenerateProgress,
    GenerateRequest,
    GenerateResponse,
    GenerationMeta,
    PromptResponse,
)
from app.services.dedup import check_duplicate, store_prompt
from app.services.generator import generate_meta_prompt, generate_prompt
from app.services.llm_provider import select_model
from app.services.persona import compose_persona
from app.services.postprocess import apply_rules

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["generate"])

_tasks: dict[str, dict] = {}


async def _load_rules(project_id: str, db: AsyncSession) -> list[PostprocessRule]:
    public_stmt = select(PostprocessRule).where(
        PostprocessRule.scope == "public",
        PostprocessRule.enabled.is_(True),
    )
    project_stmt = select(PostprocessRule).where(
        PostprocessRule.scope == "project",
        PostprocessRule.project_id == project_id,
        PostprocessRule.enabled.is_(True),
    )
    public_result = await db.execute(public_stmt)
    project_result = await db.execute(project_stmt)
    public_rules = list(public_result.scalars().all())
    project_rules = list(project_result.scalars().all())
    merged: dict[str, PostprocessRule] = {r.name: r for r in public_rules}
    for r in project_rules:
        merged[r.name] = r
    return list(merged.values())


def _get_threshold(request: GenerateRequest, project: Project) -> float:
    settings = get_settings()
    if request.similarity_threshold is not None:
        return request.similarity_threshold
    project_threshold = project.config.get("similarity_threshold")
    if project_threshold is not None:
        return float(project_threshold)
    return settings.SIMILARITY_THRESHOLD


async def _generate_single(
    project_id: str,
    task_domain: str,
    human_likeness: str,
    source_models: list[str],
    threshold: float,
    rules: list[PostprocessRule],
    db: AsyncSession,
) -> Optional[tuple[PromptResponse, str]]:
    max_retries = 5
    for attempt in range(max_retries + 1):
        persona = await compose_persona(project_id, db)
        meta_prompt = await generate_meta_prompt(persona, task_domain, db, project_id)

        try:
            model_config = await select_model(project_id, source_models, db)
        except ValueError as exc:
            raise ModelUnavailableError(last_error=str(exc)) from exc

        raw_text = await generate_prompt(meta_prompt, model_config)
        processed_text = apply_rules(raw_text, rules, human_likeness)

        is_dup, _ = await check_duplicate(processed_text, project_id, threshold, db)

        if not is_dup:
            prompt_id = str(uuid.uuid4())
            prompt_data = {
                "id": prompt_id,
                "project_id": project_id,
                "text": processed_text,
                "persona_snapshot": {
                    "occupations": persona.occupations,
                    "moods": persona.moods,
                    "language_habits": persona.language_habits,
                    "typing_habits": persona.typing_habits,
                    "scenes": persona.scenes,
                    "education": persona.education,
                },
                "source_model": model_config.name,
                "dedup_skipped": False,
                "task_domain": task_domain,
            }
            prompt = await store_prompt(prompt_data, db)
            return PromptResponse.model_validate(prompt), model_config.name

        if attempt < max_retries:
            logger.info(
                "Duplicate detected, retrying attempt %d/%d for project %s",
                attempt + 1,
                max_retries,
                project_id,
            )

    logger.warning("Max retries reached, dropping prompt for project %s", project_id)
    return None


async def _run_batch_generation(
    task_id: str,
    request: GenerateRequest,
) -> None:
    async with async_session_factory() as db:
        try:
            project = await db.get(Project, request.project_id)
            if project is None:
                raise ProjectNotFoundError(request.project_id)

            threshold = _get_threshold(request, project)
            rules = await _load_rules(request.project_id, db)
            settings = get_settings()
            semaphore = asyncio.Semaphore(settings.GENERATION_CONCURRENCY)

            prompts: list[PromptResponse] = []
            dedup_drop_count = 0
            model_usage: dict[str, int] = {}
            total_start = time.monotonic()

            async def generate_one() -> Optional[tuple[PromptResponse, str]]:
                async with semaphore:
                    return await _generate_single(
                        project_id=request.project_id,
                        task_domain=request.task_domain,
                        human_likeness=request.human_likeness,
                        source_models=request.source_models,
                        threshold=threshold,
                        rules=rules,
                        db=db,
                    )

            coros = [generate_one() for _ in range(request.count)]

            for future in asyncio.as_completed(coros):
                result = await future
                if result is not None:
                    prompt_resp, model_name = result
                    prompts.append(prompt_resp)
                    model_usage[model_name] = model_usage.get(model_name, 0) + 1
                else:
                    dedup_drop_count += 1

                completed = len(prompts) + dedup_drop_count
                _tasks[task_id]["completed"] = completed
                _tasks[task_id]["progress"] = min(completed / request.count, 1.0)

            total_time = time.monotonic() - total_start

            await db.commit()

            meta = GenerationMeta(
                total_requested=request.count,
                total_generated=len(prompts),
                dedup_drop_count=dedup_drop_count,
                total_time_ms=total_time * 1000,
                model_usage=model_usage,
            )
            response = GenerateResponse(
                project_id=request.project_id,
                prompts=prompts,
                generation_meta=meta,
            )

            _tasks[task_id]["status"] = "completed"
            _tasks[task_id]["progress"] = 1.0
            _tasks[task_id]["completed"] = request.count
            _tasks[task_id]["result"] = response

            logger.info(
                "Generation task %s completed: generated=%d, dropped=%d, elapsed=%.2fs",
                task_id,
                len(prompts),
                dedup_drop_count,
                total_time,
            )

        except Exception as exc:
            logger.exception("Generation task %s failed: %s", task_id, exc)
            _tasks[task_id]["status"] = "failed"
            _tasks[task_id]["error"] = str(exc)


@router.post("/generate", response_model=GenerateResponse)
async def generate(body: GenerateRequest, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, body.project_id)
    if project is None:
        raise ProjectNotFoundError(body.project_id)

    threshold = _get_threshold(body, project)
    rules = await _load_rules(body.project_id, db)
    settings = get_settings()
    semaphore = asyncio.Semaphore(settings.GENERATION_CONCURRENCY)

    prompts: list[PromptResponse] = []
    dedup_drop_count = 0
    dedup_skip_count = 0
    model_usage: dict[str, int] = {}
    total_start = time.monotonic()

    async def generate_one() -> Optional[tuple[PromptResponse, str]]:
        nonlocal dedup_skip_count
        async with semaphore:
            max_retries = 5
            for attempt in range(max_retries + 1):
                persona = await compose_persona(body.project_id, db)
                meta_prompt = await generate_meta_prompt(persona, body.task_domain, db, body.project_id)

                try:
                    model_config = await select_model(body.project_id, body.source_models, db)
                except ValueError as exc:
                    raise ModelUnavailableError(last_error=str(exc)) from exc

                model_usage[model_config.name] = model_usage.get(model_config.name, 0) + 1

                raw_text = await generate_prompt(meta_prompt, model_config)
                processed_text = apply_rules(raw_text, rules, body.human_likeness)

                is_dup, _ = await check_duplicate(processed_text, body.project_id, threshold, db)

                if not is_dup:
                    prompt_id = str(uuid.uuid4())
                    prompt_data = {
                        "id": prompt_id,
                        "project_id": body.project_id,
                        "text": processed_text,
                        "persona_snapshot": {
                            "occupations": persona.occupations,
                            "moods": persona.moods,
                            "language_habits": persona.language_habits,
                            "typing_habits": persona.typing_habits,
                            "scenes": persona.scenes,
                            "education": persona.education,
                        },
                        "source_model": model_config.name,
                        "dedup_skipped": False,
                        "task_domain": body.task_domain,
                    }
                    prompt = await store_prompt(prompt_data, db)
                    return PromptResponse.model_validate(prompt), model_config.name

                if attempt < max_retries:
                    dedup_skip_count += 1
                    logger.info(
                        "Duplicate detected, retrying attempt %d/%d for project %s",
                        attempt + 1,
                        max_retries,
                        body.project_id,
                    )

            logger.warning("Max retries reached, dropping prompt for project %s", body.project_id)
            return None

    coros = [generate_one() for _ in range(body.count)]
    results = await asyncio.gather(*coros)

    for r in results:
        if r is not None:
            prompt_resp, _ = r
            prompts.append(prompt_resp)
        else:
            dedup_drop_count += 1

    total_time = time.monotonic() - total_start

    meta = GenerationMeta(
        total_requested=body.count,
        total_generated=len(prompts),
        dedup_drop_count=dedup_drop_count,
        dedup_skip_count=dedup_skip_count,
        total_time_ms=total_time * 1000,
        model_usage=model_usage,
    )

    logger.info(
        "Sync generation completed: requested=%d, generated=%d, dedup_skip=%d, dedup_drop=%d, elapsed=%.2fs",
        body.count,
        len(prompts),
        dedup_skip_count,
        dedup_drop_count,
        total_time,
    )

    return GenerateResponse(
        project_id=body.project_id,
        prompts=prompts,
        generation_meta=meta,
    )


@router.post("/generate/async", response_model=GenerateAsyncResponse)
async def generate_async(body: GenerateRequest):
    task_id = uuid.uuid4().hex[:16]

    _tasks[task_id] = {
        "task_id": task_id,
        "project_id": body.project_id,
        "status": "running",
        "progress": 0.0,
        "completed": 0,
        "total": body.count,
        "result": None,
        "error": None,
    }

    asyncio.create_task(_run_batch_generation(task_id, body))

    logger.info("Started async generation task %s for project %s", task_id, body.project_id)
    return GenerateAsyncResponse(task_id=task_id, project_id=body.project_id, status="running")


@router.get("/generate/{task_id}/stream")
async def stream_generation(task_id: str):
    async def event_generator():
        while True:
            task = _tasks.get(task_id)
            if task is None:
                yield f"event: error\ndata: {{\"error\": \"Task {task_id} not found\"}}\n\n"
                break

            progress = GenerateProgress(
                task_id=task_id,
                status=task["status"],
                progress=task["progress"],
                completed=task["completed"],
                total=task["total"],
                result=task["result"],
            )
            yield f"data: {progress.model_dump_json()}\n\n"

            if task["status"] in ("completed", "failed"):
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/generate/{task_id}")
async def get_task_status(task_id: str):
    task = _tasks.get(task_id)
    if task is None:
        raise AppException(
            code="TASK_NOT_FOUND",
            message=f"Task {task_id} not found",
            status_code=404,
            detail={"task_id": task_id},
        )
    return task
