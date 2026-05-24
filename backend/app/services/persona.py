from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PersonaTrait

logger = logging.getLogger(__name__)


@dataclass
class Persona:
    occupations: list[str] = field(default_factory=list)
    moods: list[str] = field(default_factory=list)
    language_habits: list[str] = field(default_factory=list)
    typing_habits: list[str] = field(default_factory=list)
    scenes: list[str] = field(default_factory=list)
    education: str = ""
    raw_traits: list[dict[str, Any]] = field(default_factory=list)


async def compose_persona(project_id: str, db: AsyncSession) -> Persona:
    public_stmt = select(PersonaTrait).where(PersonaTrait.scope == "public")
    public_result = await db.execute(public_stmt)
    public_traits: list[PersonaTrait] = list(public_result.scalars().all())

    project_stmt = select(PersonaTrait).where(
        PersonaTrait.scope == "project",
        PersonaTrait.project_id == project_id,
    )
    project_result = await db.execute(project_stmt)
    project_traits: list[PersonaTrait] = list(project_result.scalars().all())

    merged = _merge_traits(public_traits, project_traits)

    category_map: dict[str, list[PersonaTrait]] = {}
    for trait in merged:
        category_map.setdefault(trait.category, []).append(trait)

    persona = Persona()
    category_to_field: dict[str, str] = {
        "occupation": "occupations",
        "mood": "moods",
        "language_habit": "language_habits",
        "typing_habit": "typing_habits",
        "scene": "scenes",
    }

    for category, field_name in category_to_field.items():
        items = category_map.get(category, [])
        sampled = _weighted_sample(items, k=random.randint(1, min(3, len(items))) if items else 0)
        setattr(persona, field_name, [t.label for t in sampled])

    education_items = category_map.get("education", [])
    if education_items:
        sampled_edu = _weighted_sample(education_items, k=1)
        persona.education = sampled_edu[0].label if sampled_edu else ""

    persona.raw_traits = [
        {
            "category": t.category,
            "label": t.label,
            "scope": t.scope,
            "weight": t.weight,
        }
        for t in merged
    ]

    logger.info(
        "Composed persona for project %s: occupations=%s, moods=%s, education=%s",
        project_id,
        persona.occupations,
        persona.moods,
        persona.education,
    )
    return persona


async def get_merged_traits(project_id: str, db: AsyncSession) -> list[PersonaTrait]:
    public_stmt = select(PersonaTrait).where(PersonaTrait.scope == "public")
    public_result = await db.execute(public_stmt)
    public_traits: list[PersonaTrait] = list(public_result.scalars().all())

    project_stmt = select(PersonaTrait).where(
        PersonaTrait.scope == "project",
        PersonaTrait.project_id == project_id,
    )
    project_result = await db.execute(project_stmt)
    project_traits: list[PersonaTrait] = list(project_result.scalars().all())

    merged = _merge_traits(public_traits, project_traits)
    logger.info(
        "Merged traits for project %s: %d total (public=%d, project=%d)",
        project_id,
        len(merged),
        len(public_traits),
        len(project_traits),
    )
    return merged


def _merge_traits(
    public_traits: list[PersonaTrait],
    project_traits: list[PersonaTrait],
) -> list[PersonaTrait]:
    trait_map: dict[tuple[str, str], PersonaTrait] = {}

    for trait in public_traits:
        key = (trait.category, trait.label)
        trait_map[key] = trait

    for trait in project_traits:
        key = (trait.category, trait.label)
        trait_map[key] = trait

    return list(trait_map.values())


def _weighted_sample(items: list[PersonaTrait], k: int) -> list[PersonaTrait]:
    if k <= 0 or not items:
        return []

    weights = [getattr(t, "weight", 1.0) or 1.0 for t in items]
    k = min(k, len(items))
    return random.choices(items, weights=weights, k=k)
