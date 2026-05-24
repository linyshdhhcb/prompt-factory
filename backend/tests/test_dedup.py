from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.dedup import check_duplicate, generate_embedding, store_prompt


@pytest.mark.asyncio
async def test_check_duplicate_returns_true_when_similar():
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_row = MagicMock()
    mock_row.similarity = 0.95
    mock_row.id = "some-id"
    mock_result.first.return_value = mock_row
    mock_db.execute.return_value = mock_result

    with patch("app.services.dedup.generate_embedding", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = [0.1] * 1536

        is_dup, similarity = await check_duplicate(
            "测试文本", "proj-1", 0.85, mock_db
        )

    assert is_dup is True
    assert similarity == 0.95


@pytest.mark.asyncio
async def test_check_duplicate_returns_false_when_different():
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_row = MagicMock()
    mock_row.similarity = 0.5
    mock_row.id = "some-id"
    mock_result.first.return_value = mock_row
    mock_db.execute.return_value = mock_result

    with patch("app.services.dedup.generate_embedding", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = [0.1] * 1536

        is_dup, similarity = await check_duplicate(
            "完全不同的文本", "proj-1", 0.85, mock_db
        )

    assert is_dup is False
    assert similarity == 0.5


@pytest.mark.asyncio
async def test_generate_embedding_returns_none_on_failure():
    with patch("app.services.dedup.AsyncOpenAI") as mock_openai_cls:
        mock_client = AsyncMock()
        mock_client.embeddings.create.side_effect = Exception("API error")
        mock_openai_cls.return_value = mock_client

        with patch("app.services.dedup.asyncio.sleep", new_callable=AsyncMock):
            result = await generate_embedding("测试文本")

    assert result is None


@pytest.mark.asyncio
async def test_store_prompt_with_embedding():
    mock_db = AsyncMock()

    with patch("app.services.dedup.generate_embedding", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = [0.1] * 1536

        prompt_data = {
            "id": "test-uuid",
            "text": "测试prompt文本",
            "project_id": "proj-1",
            "persona_snapshot": {"mood": "开心"},
            "source_model": "gpt-4o-mini",
            "task_domain": "技术问答",
        }

        prompt = await store_prompt(prompt_data, mock_db)

    mock_db.add.assert_called_once()
    mock_db.flush.assert_awaited_once()

    added_obj = mock_db.add.call_args[0][0]
    assert added_obj.id == "test-uuid"
    assert added_obj.text == "测试prompt文本"
    assert added_obj.project_id == "proj-1"
    assert added_obj.source_model == "gpt-4o-mini"
    assert added_obj.task_domain == "技术问答"
    assert added_obj.embedding is not None
