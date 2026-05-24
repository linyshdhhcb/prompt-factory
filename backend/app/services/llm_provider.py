from __future__ import annotations

import json
import logging
import os
import random
from abc import ABC, abstractmethod

from openai import APIConnectionError, AsyncOpenAI, RateLimitError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.models.schemas import ModelConfigInternal

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...


class OpenAIProvider(LLMProvider):
    def __init__(self, model_config: ModelConfigInternal) -> None:
        self.model_config = model_config
        self.client = AsyncOpenAI(
            base_url=model_config.base_url,
            api_key=model_config.api_key or "no-key",
        )
        self.model_name = model_config.model_name

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception_type((APIConnectionError, RateLimitError)),
    )
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        logger.info(
            "Generating with model=%s, temperature=%.2f, max_tokens=%d",
            self.model_name,
            temperature,
            max_tokens,
        )
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content or ""
        logger.info("Generation complete, length=%d", len(content))
        return content

    async def health_check(self) -> bool:
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "ping"}],
                temperature=0.0,
                max_tokens=5,
            )
            return bool(response.choices)
        except (APIConnectionError, RateLimitError):
            logger.warning("Health check failed for model %s", self.model_name)
            return False
        except Exception:
            logger.exception("Unexpected error during health check for model %s", self.model_name)
            return False


class AnthropicProvider(LLMProvider):
    def __init__(self, model_config: ModelConfigInternal) -> None:
        self.model_config = model_config
        self.api_key = model_config.api_key or ""
        self.base_url = model_config.base_url
        self.model_name = model_config.model_name

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
    )
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        import httpx

        logger.info(
            "Generating with Anthropic model=%s, temperature=%.2f, max_tokens=%d",
            self.model_name,
            temperature,
            max_tokens,
        )
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }

        url = f"{self.base_url}/messages"
        async with httpx.AsyncClient(timeout=self.model_config.timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        content = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")

        logger.info("Anthropic generation complete, length=%d", len(content))
        return content

    async def health_check(self) -> bool:
        try:
            result = await self.generate(
                system_prompt="You are a helpful assistant.",
                user_prompt="ping",
                temperature=0.0,
                max_tokens=5,
            )
            return len(result) > 0
        except Exception:
            logger.warning("Anthropic health check failed for model %s", self.model_name)
            return False


class AzureOpenAIProvider(LLMProvider):
    def __init__(self, model_config: ModelConfigInternal) -> None:
        self.model_config = model_config
        self.api_key = model_config.api_key or ""
        self.base_url = model_config.base_url
        self.model_name = model_config.model_name
        self.deployment_name = model_config.model_name

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
    )
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        import httpx

        logger.info(
            "Generating with Azure OpenAI deployment=%s, temperature=%.2f, max_tokens=%d",
            self.deployment_name,
            temperature,
            max_tokens,
        )
        url = (
            f"{self.base_url}/openai/deployments/{self.deployment_name}"
            f"/chat/completions?api-version=2024-02-15-preview"
        )
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=self.model_config.timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]
        logger.info("Azure OpenAI generation complete, length=%d", len(content))
        return content

    async def health_check(self) -> bool:
        try:
            result = await self.generate(
                system_prompt="You are a helpful assistant.",
                user_prompt="ping",
                temperature=0.0,
                max_tokens=5,
            )
            return len(result) > 0
        except Exception:
            logger.warning("Azure OpenAI health check failed for deployment %s", self.deployment_name)
            return False


class BedrockProvider(LLMProvider):
    def __init__(self, model_config: ModelConfigInternal) -> None:
        self.model_config = model_config
        self.model_name = model_config.model_name
        self.base_url = model_config.base_url
        self._region = self._extract_region()

    def _extract_region(self) -> str:
        if "bedrock" in self.base_url or "amazonaws" in self.base_url:
            parts = self.base_url.replace("https://", "").split(".")
            if len(parts) >= 1:
                return parts[0]
        return os.environ.get("AWS_REGION", "us-east-1")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
    )
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        import httpx

        logger.info(
            "Generating with Bedrock model=%s, temperature=%.2f, max_tokens=%d",
            self.model_name,
            temperature,
            max_tokens,
        )

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        })

        url = (
            f"https://bedrock-runtime.{self._region}.amazonaws.com"
            f"/model/{self.model_name}/invoke"
        )

        aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID", "")
        aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
        aws_session_token = os.environ.get("AWS_SESSION_TOKEN", "")

        headers = self._sign_request("POST", url, body, aws_access_key, aws_secret_key, aws_session_token)
        headers["Content-Type"] = "application/json"

        async with httpx.AsyncClient(timeout=self.model_config.timeout) as client:
            response = await client.post(url, headers=headers, content=body)
            response.raise_for_status()
            data = response.json()

        content = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")

        logger.info("Bedrock generation complete, length=%d", len(content))
        return content

    def _sign_request(
        self,
        method: str,
        url: str,
        body: str,
        access_key: str,
        secret_key: str,
        session_token: str = "",
    ) -> dict[str, str]:
        from datetime import datetime, timezone
        import hashlib
        import hmac

        parsed = __import__("urllib.parse", fromlist=["urlparse"]).urlparse(url)
        host = parsed.netloc
        amz_date = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        date_stamp = datetime.now(timezone.utc).strftime("%Y%m%d")

        payload_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()

        canonical_headers = f"content-type:application/json\nhost:{host}\nx-amz-date:{amz_date}\n"
        if session_token:
            canonical_headers += f"x-amz-security-token:{session_token}\n"
        signed_headers = "content-type;host;x-amz-date"
        if session_token:
            signed_headers += ";x-amz-security-token"

        canonical_request = f"{method}\n{parsed.path}\n\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
        credential_scope = f"{date_stamp}/{self._region}/bedrock/aws4_request"
        string_to_sign = f"AWS4-HMAC-SHA256\n{amz_date}\n{credential_scope}\n" + hashlib.sha256(
            canonical_request.encode("utf-8")
        ).hexdigest()

        def sign(key: bytes, msg: str) -> bytes:
            return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

        signing_key = sign(sign(sign(sign(("AWS4" + secret_key).encode("utf-8")), date_stamp), self._region), "bedrock")
        signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        auth_header = f"AWS4-HMAC-SHA256 Credential={access_key}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"

        headers = {
            "Content-Type": "application/json",
            "Host": host,
            "X-Amz-Date": amz_date,
            "Authorization": auth_header,
        }
        if session_token:
            headers["X-Amz-Security-Token"] = session_token

        return headers

    async def health_check(self) -> bool:
        try:
            result = await self.generate(
                system_prompt="You are a helpful assistant.",
                user_prompt="ping",
                temperature=0.0,
                max_tokens=5,
            )
            return len(result) > 0
        except Exception:
            logger.warning("Bedrock health check failed for model %s", self.model_name)
            return False


async def select_model(
    project_id: str,
    source_models: list[str],
    db: AsyncSession,
) -> ModelConfigInternal:
    from app.models import ModelConfig as ModelConfigORM

    if source_models:
        stmt = select(ModelConfigORM).where(
            ModelConfigORM.name.in_(source_models),
            ModelConfigORM.enabled.is_(True),
        )
        result = await db.execute(stmt)
        models: list[ModelConfigORM] = list(result.scalars().all())
    else:
        public_stmt = select(ModelConfigORM).where(
            ModelConfigORM.scope == "public",
            ModelConfigORM.enabled.is_(True),
        )
        project_stmt = select(ModelConfigORM).where(
            ModelConfigORM.scope == "project",
            ModelConfigORM.project_id == project_id,
            ModelConfigORM.enabled.is_(True),
        )

        public_result = await db.execute(public_stmt)
        public_models: list[ModelConfigORM] = list(public_result.scalars().all())

        project_result = await db.execute(project_stmt)
        project_models: list[ModelConfigORM] = list(project_result.scalars().all())

        merged: dict[str, ModelConfigORM] = {m.name: m for m in public_models}
        for m in project_models:
            merged[m.name] = m

        models = list(merged.values())

    if not models:
        raise ValueError(f"No models available for project {project_id}")

    weights = [getattr(m, "weight", 1.0) or 1.0 for m in models]
    selected = random.choices(models, weights=weights, k=1)[0]
    return _orm_to_schema(selected)


def get_provider(model_config: ModelConfigInternal) -> LLMProvider:
    provider_type = getattr(model_config, "provider_type", "openai") or "openai"

    if provider_type == "anthropic":
        return AnthropicProvider(model_config)
    elif provider_type == "azure":
        return AzureOpenAIProvider(model_config)
    elif provider_type == "bedrock":
        return BedrockProvider(model_config)
    else:
        return OpenAIProvider(model_config)


def _orm_to_schema(orm_obj: object) -> ModelConfigInternal:
    from app.core.crypto import decrypt_api_key

    api_key_encrypted = getattr(orm_obj, "api_key_encrypted", None)
    api_key = decrypt_api_key(api_key_encrypted) if api_key_encrypted else ""

    return ModelConfigInternal(
        id=orm_obj.id,
        name=orm_obj.name,
        provider_type=getattr(orm_obj, "provider_type", "openai") or "openai",
        api_key=api_key,
        base_url=orm_obj.base_url,
        model_name=orm_obj.model_name,
        weight=orm_obj.weight,
        max_tokens=orm_obj.max_tokens,
        timeout=orm_obj.timeout,
        scope=orm_obj.scope,
        project_id=orm_obj.project_id,
        enabled=orm_obj.enabled,
        created_at=orm_obj.created_at,
        updated_at=orm_obj.updated_at,
    )
