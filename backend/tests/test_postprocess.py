from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from app.services.postprocess import (
    HUMAN_LIKENESS_MULTIPLIER,
    _prefix_filler,
    _replace_de,
    apply_rules,
)


@dataclass
class MockPostprocessRule:
    id: int = 1
    name: str = ""
    description: str = ""
    probability: float = 1.0
    params: dict[str, Any] = field(default_factory=dict)
    scope: str = "public"
    project_id: str | None = None
    enabled: bool = True
    sort_order: int = 0


def test_apply_rules_with_probability_one():
    rules = [
        MockPostprocessRule(name="prefix_filler", probability=1.0, sort_order=1, params={"fillers": ["嗯"]}),
    ]
    result = apply_rules("你好世界", rules, "high")
    assert result.startswith("嗯")


def test_apply_rules_with_probability_zero():
    rules = [
        MockPostprocessRule(name="prefix_filler", probability=0.0, sort_order=1),
        MockPostprocessRule(name="replace_de", probability=0.0, sort_order=2),
    ]
    text = "我的世界的"
    result = apply_rules(text, rules, "high")
    assert result == text


def test_human_likeness_multiplier_low():
    multiplier = HUMAN_LIKENESS_MULTIPLIER["low"]
    assert multiplier == 0.3

    rules = [
        MockPostprocessRule(name="prefix_filler", probability=1.0, sort_order=1, params={"fillers": ["嗯"]}),
    ]
    n_applied = 0
    n_total = 10000
    for _ in range(n_total):
        result = apply_rules("你好", rules, "low")
        if result.startswith("嗯"):
            n_applied += 1

    observed_prob = n_applied / n_total
    expected_prob = min(1.0 * 0.3, 1.0)
    assert abs(observed_prob - expected_prob) < 0.05


def test_human_likeness_multiplier_insane():
    multiplier = HUMAN_LIKENESS_MULTIPLIER["insane"]
    assert multiplier == 1.5

    rules = [
        MockPostprocessRule(name="prefix_filler", probability=0.8, sort_order=1, params={"fillers": ["嗯"]}),
    ]
    n_applied = 0
    n_total = 10000
    for _ in range(n_total):
        result = apply_rules("你好", rules, "insane")
        if result.startswith("嗯"):
            n_applied += 1

    observed_prob = n_applied / n_total
    assert observed_prob > 0.9


def test_prefix_filler_rule():
    text = "你好世界"
    result = _prefix_filler(text, {"fillers": ["嗯"]})
    assert result == "嗯你好世界"


def test_replace_de_rule():
    text = "我的世界的"
    result = _replace_de(text, {"probability": 1.0})
    assert result == "我滴世界滴"


def test_rules_execute_in_sort_order():
    rules = [
        MockPostprocessRule(name="replace_de", probability=1.0, sort_order=2, params={"probability": 1.0}),
        MockPostprocessRule(name="prefix_filler", probability=1.0, sort_order=1, params={"fillers": ["嗯"]}),
    ]
    result = apply_rules("我的世界", rules, "high")
    assert result.startswith("嗯")
    assert "滴" in result
