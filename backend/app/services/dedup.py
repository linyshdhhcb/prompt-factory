from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from openai import AsyncOpenAI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import Prompt

logger = logging.getLogger(__name__)


async def check_duplicate(
    text_str: str,
    project_id: str,
    threshold: float,
    db: AsyncSession,
) -> tuple[bool, float]:
    embedding = await generate_embedding(text_str)
    if embedding is None:
        logger.warning(
            "Embedding generation failed, skipping dedup for project %s",
            project_id,
        )
        return (False, 0.0)

    embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"
    query = text(
        """
        SELECT id, 1 - (embedding <=> :embedding::vector) AS similarity
        FROM prompts
        WHERE project_id = :project_id
        ORDER BY embedding <=> :embedding::vector
        LIMIT 1
        """
    )
    result = await db.execute(
        query,
        {"embedding": embedding_str, "project_id": project_id},
    )
    row = result.first()

    if row is None:
        logger.info("No existing prompts found for project %s", project_id)
        return (False, 0.0)

    similarity = float(row.similarity)
    is_dup = similarity > threshold
    logger.info(
        "Dedup check for project %s: similarity=%.4f, threshold=%.4f, is_duplicate=%s",
        project_id,
        similarity,
        threshold,
        is_dup,
    )
    return (is_dup, similarity)


async def generate_embedding(text_str: str) -> list[float] | None:
    settings = get_settings()
    api_key = os.environ.get(settings.EMBEDDING_API_KEY_ENV, "")
    backoff_delays: list[float] = [1.0, 2.0, 4.0]

    for attempt, delay in enumerate(backoff_delays, start=1):
        try:
            client = AsyncOpenAI(
                base_url=settings.EMBEDDING_BASE_URL,
                api_key=api_key,
            )
            response = await client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=text_str,
            )
            embedding = response.data[0].embedding
            logger.info(
                "Generated embedding, dim=%d, attempt=%d",
                len(embedding),
                attempt,
            )
            return embedding
        except Exception as exc:
            logger.warning(
                "Embedding generation attempt %d failed: %s",
                attempt,
                str(exc),
            )
            if attempt < len(backoff_delays):
                await asyncio.sleep(delay)

    logger.warning(
        "All embedding generation attempts failed for text (len=%d)",
        len(text_str),
    )
    return None


async def store_prompt(
    prompt_data: dict[str, Any],
    db: AsyncSession,
) -> Prompt:
    text_str = prompt_data.get("text", "")
    project_id = prompt_data.get("project_id", "")

    embedding = await generate_embedding(text_str)

    prompt = Prompt(
        id=prompt_data.get("id"),
        text=text_str,
        project_id=project_id,
        embedding=embedding,
        persona_snapshot=prompt_data.get("persona_snapshot", {}),
        source_model=prompt_data.get("source_model"),
        dedup_skipped=prompt_data.get("dedup_skipped", embedding is None),
        task_domain=prompt_data.get("task_domain"),
    )

    db.add(prompt)
    await db.flush()

    logger.info(
        "Stored prompt id=%s for project %s, embedding=%s",
        prompt.id,
        project_id,
        "present" if embedding is not None else "missing",
    )
    return prompt
