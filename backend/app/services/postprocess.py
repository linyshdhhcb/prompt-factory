from __future__ import annotations

import logging
import random
import re

from app.models import PostprocessRule

logger = logging.getLogger(__name__)

HUMAN_LIKENESS_MULTIPLIER: dict[str, float] = {
    "low": 0.3,
    "medium": 0.6,
    "high": 1.0,
    "insane": 1.5,
}

DEFAULT_FILLERS: list[str] = ["嗯", "啊", "哦", "那个"]
DEFAULT_FILLER_WORDS: list[str] = ["唔", "额", "那个"]


def apply_rules(
    text: str,
    rules: list[PostprocessRule],
    human_likeness: str,
) -> str:
    multiplier = HUMAN_LIKENESS_MULTIPLIER.get(human_likeness, 0.6)
    sorted_rules = sorted(rules, key=lambda r: r.sort_order)

    for rule in sorted_rules:
        if not rule.enabled:
            continue
        actual_prob = min(rule.probability * multiplier, 1.0)
        if random.random() < actual_prob:
            logger.debug(
                "Applying rule %s (prob=%.3f, actual_prob=%.3f)",
                rule.name,
                rule.probability,
                actual_prob,
            )
            text = apply_rule(text, rule)

    return text


def apply_rule(text: str, rule: PostprocessRule) -> str:
    params = rule.params if rule.params else {}
    handler = _RULE_HANDLERS.get(rule.name)
    if handler is None:
        logger.warning("Unknown postprocess rule: %s", rule.name)
        return text
    return handler(text, params)


def _prefix_filler(text: str, params: dict) -> str:
    fillers = params.get("fillers", DEFAULT_FILLERS)
    filler = random.choice(fillers)
    return f"{filler}{text}"


def _replace_de(text: str, params: dict) -> str:
    probability = params.get("probability", 0.3)
    result = []
    for char in text:
        if char == "的" and random.random() < probability:
            result.append("滴")
        else:
            result.append(char)
    return "".join(result)


def _randomize_punctuation(text: str, params: dict) -> str:
    result = []
    for char in text:
        if char == "。" and random.random() < 0.4:
            result.append("..")
        elif char == "，" and random.random() < 0.2:
            continue
        else:
            result.append(char)
    return "".join(result)


def _insert_filler_words(text: str, params: dict) -> str:
    filler_words = params.get("filler_words", DEFAULT_FILLER_WORDS)
    max_insertions = params.get("max_insertions", 2)

    if not text:
        return text

    chars = list(text)
    eligible_positions = [i for i in range(1, len(chars)) if chars[i] not in (" ", "\n", "。", "，", "！", "？")]
    if not eligible_positions:
        return text

    insert_count = min(random.randint(1, max_insertions), len(eligible_positions))
    positions = sorted(random.sample(eligible_positions, k=insert_count), reverse=True)

    for pos in positions:
        filler = random.choice(filler_words)
        chars.insert(pos, filler)

    return "".join(chars)


def _lowercase_start(text: str, params: dict) -> str:
    probability = params.get("probability", 0.5)
    if not text:
        return text
    if text[0].isupper() and random.random() < probability:
        return text[0].lower() + text[1:]
    return text


def _mess_spacing(text: str, params: dict) -> str:
    add_prob = params.get("add_space_probability", 0.3)
    remove_prob = params.get("remove_space_probability", 0.5)

    result = re.sub(
        r'([\u4e00-\u9fff])([a-zA-Z])',
        lambda m: f"{m.group(1)} {m.group(2)}" if random.random() < add_prob else m.group(0),
        text,
    )
    result = re.sub(
        r'([\u4e00-\u9fff]) ([a-zA-Z])',
        lambda m: f"{m.group(1)}{m.group(2)}" if random.random() < remove_prob else m.group(0),
        result,
    )
    result = re.sub(
        r'([a-zA-Z])([\u4e00-\u9fff])',
        lambda m: f"{m.group(1)} {m.group(2)}" if random.random() < add_prob else m.group(0),
        result,
    )
    result = re.sub(
        r'([a-zA-Z]) ([\u4e00-\u9fff])',
        lambda m: f"{m.group(1)}{m.group(2)}" if random.random() < remove_prob else m.group(0),
        result,
    )

    return result


def _remove_punctuation(text: str, params: dict) -> str:
    probability = params.get("probability", 0.2)
    punctuation_marks = params.get("punctuation_marks", ["。", "，", "！", "？", "；", "："])
    result = []
    for char in text:
        if char in punctuation_marks and random.random() < probability:
            continue
        result.append(char)
    return "".join(result)


_RULE_HANDLERS: dict[str, callable] = {
    "prefix_filler": _prefix_filler,
    "replace_de": _replace_de,
    "randomize_punctuation": _randomize_punctuation,
    "insert_filler_words": _insert_filler_words,
    "lowercase_start": _lowercase_start,
    "mess_spacing": _mess_spacing,
    "remove_punctuation": _remove_punctuation,
}
