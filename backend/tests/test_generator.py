from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.generator import (
    ADDITIONAL_CONSTRAINT_POOL,
    _build_variables,
    _interpolate_template,
)
from app.services.persona import Persona


def test_build_variables_contains_all_keys():
    persona = Persona(
        occupations=["程序员"],
        moods=["开心"],
        language_habits=["说脏话"],
        typing_habits=["快速打字"],
        scenes=["办公室"],
        education="本科",
    )

    variables = _build_variables(persona, "技术问答")

    assert "role" in variables
    assert "scene" in variables
    assert "mood" in variables
    assert "quirk" in variables
    assert "domain" in variables
    assert variables["domain"] == "技术问答"
    assert variables["role"] == "程序员"
    assert variables["scene"] == "办公室"
    assert variables["mood"] == "开心"
    assert variables["quirk"] == "说脏话"


def test_interpolate_template_replaces_variables():
    template = "你是一个{{role}}，在{{scene}}中，情绪{{mood}}，习惯{{quirk}}，领域{{domain}}"
    variables = {
        "role": "程序员",
        "scene": "办公室",
        "mood": "开心",
        "quirk": "说脏话",
        "domain": "技术问答",
    }

    result = _interpolate_template(template, variables)

    assert "程序员" in result
    assert "办公室" in result
    assert "开心" in result
    assert "说脏话" in result
    assert "技术问答" in result
    assert "{{" not in result


def test_interpolate_template_preserves_unknown():
    template = "你好{{role}}，未知变量{{unknown_var}}"
    variables = {"role": "程序员"}

    result = _interpolate_template(template, variables)

    assert "程序员" in result
    assert "{{unknown_var}}" in result


@pytest.mark.asyncio
async def test_additional_constraints_appended():
    with patch("app.services.generator.random") as mock_random:
        mock_random.randint.side_effect = [2, 1]
        mock_random.choice.return_value = "使用短句为主，每句不超过15字"
        mock_random.sample.return_value = [ADDITIONAL_CONSTRAINT_POOL[0]]
        mock_random.choices.return_value = [MagicMock()]
        mock_random.shuffle.return_value = None

        persona = Persona(
            occupations=["程序员"],
            moods=["开心"],
            scenes=["办公室"],
            language_habits=["说脏话"],
        )

        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.template = "你是一个{{role}}"
        mock_template.weight = 1.0

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_template]
        mock_db.execute.return_value = mock_result

        from app.services.generator import generate_meta_prompt

        result = await generate_meta_prompt(persona, "技术问答", mock_db, "proj-1")

        assert "错别字" in result
        assert ADDITIONAL_CONSTRAINT_POOL[0] in result
