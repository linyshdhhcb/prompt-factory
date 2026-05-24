from __future__ import annotations

import logging
import random
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MetaPromptTemplate
from app.models.schemas import ModelConfig
from app.services.llm_provider import get_provider
from app.services.persona import Persona

logger = logging.getLogger(__name__)

ADDITIONAL_CONSTRAINT_POOL: list[str] = [
    "字数控制在30字以内",
    "必须包含一个反问句",
    "不要使用任何标点符号",
    "必须包含一个网络用语",
    "句子必须以感叹号结尾",
    "必须提到一个具体时间",
    "必须包含一个数字",
]

SENTENCE_STRUCTURES: list[str] = [
    "使用短句为主，每句不超过15字",
    "使用长句，包含至少一个从句",
    "使用倒装句式",
    "使用排比句式",
    "使用设问句式",
]


async def generate_meta_prompt(
    persona: Persona,
    task_domain: str,
    db: AsyncSession,
    project_id: str,
) -> str:
    public_stmt = select(MetaPromptTemplate).where(
        MetaPromptTemplate.scope == "public",
        MetaPromptTemplate.enabled.is_(True),
    )
    public_result = await db.execute(public_stmt)
    public_templates: list[MetaPromptTemplate] = list(public_result.scalars().all())

    project_stmt = select(MetaPromptTemplate).where(
        MetaPromptTemplate.scope == "project",
        MetaPromptTemplate.project_id == project_id,
        MetaPromptTemplate.enabled.is_(True),
    )
    project_result = await db.execute(project_stmt)
    project_templates: list[MetaPromptTemplate] = list(project_result.scalars().all())

    merged: dict[int, MetaPromptTemplate] = {t.id: t for t in public_templates}
    for t in project_templates:
        merged[t.id] = t

    templates = list(merged.values())
    if not templates:
        raise ValueError(f"No enabled templates found for project {project_id}")

    weights = [getattr(t, "weight", 1.0) or 1.0 for t in templates]
    selected_template = random.choices(templates, weights=weights, k=1)[0]

    variables = _build_variables(persona, task_domain)

    meta_prompt = _interpolate_template(selected_template.template, variables)

    typo_count = random.randint(1, 3)
    sentence_constraint = random.choice(SENTENCE_STRUCTURES)
    meta_prompt += f"\n\n请故意制造{typo_count}个错别字。"
    meta_prompt += f"\n{sentence_constraint}。"

    additional_count = random.randint(0, 2)
    if additional_count > 0:
        additional = random.sample(
            ADDITIONAL_CONSTRAINT_POOL,
            k=min(additional_count, len(ADDITIONAL_CONSTRAINT_POOL)),
        )
        for constraint in additional:
            meta_prompt += f"\n{constraint}。"

    logger.info(
        "Generated meta-prompt for project %s, template_id=%s, length=%d",
        project_id,
        selected_template.id,
        len(meta_prompt),
    )
    return meta_prompt


async def generate_prompt(
    meta_prompt: str,
    model_config: ModelConfig,
) -> str:
    provider = get_provider(model_config)
    result = await provider.generate(
        system_prompt=meta_prompt,
        user_prompt="请提出你的问题",
        temperature=0.9,
        max_tokens=model_config.max_tokens,
    )
    logger.info("Generated prompt, length=%d", len(result))
    return result


def _build_variables(persona: Persona, task_domain: str) -> dict[str, str]:
    role = random.choice(persona.occupations) if persona.occupations else "普通人"
    scene = random.choice(persona.scenes) if persona.scenes else "日常场景"
    mood = random.choice(persona.moods) if persona.moods else "平静"
    quirk = random.choice(persona.language_habits) if persona.language_habits else "无特殊习惯"

    descriptions = []
    if persona.occupations:
        descriptions.append(f"职业背景：{'、'.join(persona.occupations)}")
    if persona.moods:
        descriptions.append(f"情绪状态：{'、'.join(persona.moods)}")
    if persona.language_habits:
        descriptions.append(f"语言习惯：{'、'.join(persona.language_habits)}")
    if persona.typing_habits:
        descriptions.append(f"打字习惯：{'、'.join(persona.typing_habits)}")
    if persona.scenes:
        descriptions.append(f"使用场景：{'、'.join(persona.scenes)}")
    if persona.education:
        descriptions.append(f"教育背景：{persona.education}")

    random.shuffle(descriptions)

    return {
        "role": role,
        "scene": scene,
        "mood": mood,
        "quirk": quirk,
        "domain": task_domain,
        "descriptions": "\n".join(descriptions),
    }


def _interpolate_template(template: str, variables: dict[str, str]) -> str:
    def replacer(match: re.Match[str]) -> str:
        key = match.group(1)
        return variables.get(key, match.group(0))

    return re.sub(r"\{\{(\w+)\}\}", replacer, template)
