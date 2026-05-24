from __future__ import annotations

import random
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PersonaTrait
from app.services.persona import Persona, _merge_traits, _weighted_sample, compose_persona


def _make_trait(
    category: str = "occupation",
    label: str = "test",
    weight: float = 1.0,
    scope: str = "public",
    project_id: str | None = None,
) -> PersonaTrait:
    trait = PersonaTrait.__new__(PersonaTrait)
    trait.category = category
    trait.label = label
    trait.weight = weight
    trait.scope = scope
    trait.project_id = project_id
    trait.traits = []
    trait.id = random.randint(1, 999999)
    return trait


@pytest.mark.asyncio
async def test_compose_persona_returns_valid_structure(db_session: AsyncSession):
    public_traits = [
        _make_trait("occupation", "程序员", 1.0, "public"),
        _make_trait("mood", "开心", 1.0, "public"),
        _make_trait("scene", "办公室", 1.0, "public"),
        _make_trait("language_habit", "说脏话", 1.0, "public"),
        _make_trait("typing_habit", "快速打字", 1.0, "public"),
        _make_trait("education", "本科", 1.0, "public"),
    ]
    for t in public_traits:
        db_session.add(t)
    await db_session.commit()

    persona = await compose_persona("test-project", db_session)

    assert isinstance(persona, Persona)
    assert isinstance(persona.occupations, list)
    assert isinstance(persona.moods, list)
    assert isinstance(persona.language_habits, list)
    assert isinstance(persona.typing_habits, list)
    assert isinstance(persona.scenes, list)
    assert isinstance(persona.education, str)
    assert isinstance(persona.raw_traits, list)


def test_merge_public_and_project_traits():
    public = [
        _make_trait("occupation", "程序员", 1.0, "public"),
        _make_trait("mood", "开心", 1.0, "public"),
    ]
    project = [
        _make_trait("occupation", "设计师", 1.0, "project", "proj-1"),
    ]

    merged = _merge_traits(public, project)

    labels = {(t.category, t.label) for t in merged}
    assert ("occupation", "程序员") in labels
    assert ("mood", "开心") in labels
    assert ("occupation", "设计师") in labels
    assert len(merged) == 3


def test_project_trait_overrides_public():
    public = [
        _make_trait("occupation", "程序员", 1.0, "public"),
    ]
    project = [
        _make_trait("occupation", "程序员", 2.0, "project", "proj-1"),
    ]

    merged = _merge_traits(public, project)

    assert len(merged) == 1
    assert merged[0].weight == 2.0
    assert merged[0].scope == "project"


def test_weighted_sampling_respects_weights():
    heavy = _make_trait("occupation", "重权重", 100.0)
    light = _make_trait("occupation", "轻权重", 1.0)
    items = [heavy, light]

    counts = {"重权重": 0, "轻权重": 0}
    n_iterations = 10000
    for _ in range(n_iterations):
        sampled = _weighted_sample(items, k=1)
        counts[sampled[0].label] += 1

    assert counts["重权重"] > counts["轻权重"]
    ratio = counts["重权重"] / n_iterations
    assert ratio > 0.8
