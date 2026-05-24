from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    id: str | None = Field(default=None, pattern=r"^[a-zA-Z0-9_-]{1,64}$", description="留空则自动生成雪花算法ID")
    name: str = Field(max_length=200)
    description: str = Field(default="", max_length=65535)
    config: dict = Field(default_factory=dict)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=65535)
    config: dict | None = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    config: dict
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int


class PersonaTraitCreate(BaseModel):
    category: str = Field(max_length=50)
    label: str = Field(max_length=200)
    traits: list = Field(default_factory=list)
    weight: float = Field(default=1.0)
    scope: Literal["public", "project"] = "public"
    project_id: str | None = Field(default=None, max_length=64)


class PersonaTraitUpdate(BaseModel):
    category: str | None = Field(default=None, max_length=50)
    label: str | None = Field(default=None, max_length=200)
    traits: list | None = None
    weight: float | None = None
    scope: Literal["public", "project"] | None = None
    project_id: str | None = Field(default=None, max_length=64)


class PersonaTraitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    label: str
    traits: list
    weight: float
    scope: str
    project_id: str | None
    created_at: datetime
    updated_at: datetime


class PersonaTraitListResponse(BaseModel):
    items: list[PersonaTraitResponse]
    total: int


class PromptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    text: str
    persona_snapshot: dict
    source_model: str | None
    dedup_skipped: bool
    task_domain: str | None
    created_at: datetime


class PromptListResponse(BaseModel):
    items: list[PromptResponse]
    total: int


class HistoryResponse(BaseModel):
    project_id: str
    total: int
    limit: int
    offset: int
    prompts: list[PromptResponse]


class MetaTemplateCreate(BaseModel):
    template: str
    scope: Literal["public", "project"] = "public"
    project_id: str | None = Field(default=None, max_length=64)
    enabled: bool = True
    weight: float = 1.0


class MetaTemplateUpdate(BaseModel):
    template: str | None = None
    scope: Literal["public", "project"] | None = None
    project_id: str | None = Field(default=None, max_length=64)
    enabled: bool | None = None
    weight: float | None = None


class MetaTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    template: str
    scope: str
    project_id: str | None
    enabled: bool
    weight: float
    created_at: datetime


class PostprocessRuleCreate(BaseModel):
    name: str = Field(max_length=100)
    description: str = ""
    probability: float = 0.1
    params: dict = Field(default_factory=dict)
    scope: Literal["public", "project"] = "public"
    project_id: str | None = Field(default=None, max_length=64)
    enabled: bool = True
    sort_order: int = 0


class PostprocessRuleUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    description: str | None = None
    probability: float | None = None
    params: dict | None = None
    scope: Literal["public", "project"] | None = None
    project_id: str | None = Field(default=None, max_length=64)
    enabled: bool | None = None
    sort_order: int | None = None


class PostprocessRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    probability: float
    params: dict
    scope: str
    project_id: str | None
    enabled: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class SortOrderItem(BaseModel):
    id: int
    sort_order: int


class SortOrderRequest(BaseModel):
    items: list[SortOrderItem]


class ModelConfigCreate(BaseModel):
    name: str = Field(max_length=50)
    provider_type: Literal["openai", "anthropic", "azure", "bedrock"] = "openai"
    api_key: str = Field(default="", max_length=500)
    base_url: str = Field(max_length=500)
    model_name: str = Field(max_length=100)
    weight: float = 1.0
    max_tokens: int = 256
    timeout: int = 30
    scope: Literal["public", "project"] = "public"
    project_id: str | None = Field(default=None, max_length=64)
    enabled: bool = True


class ModelConfigUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=50)
    provider_type: Literal["openai", "anthropic", "azure", "bedrock"] | None = None
    api_key: str | None = Field(default=None, max_length=500)
    base_url: str | None = Field(default=None, max_length=500)
    model_name: str | None = Field(default=None, max_length=100)
    weight: float | None = None
    max_tokens: int | None = None
    timeout: int | None = None
    scope: Literal["public", "project"] | None = None
    project_id: str | None = Field(default=None, max_length=64)
    enabled: bool | None = None


class ModelConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    provider_type: str
    api_key_masked: str = ""
    base_url: str
    model_name: str
    weight: float
    max_tokens: int
    timeout: int
    scope: str
    project_id: str | None
    enabled: bool
    created_at: datetime
    updated_at: datetime


class GenerationMeta(BaseModel):
    total_requested: int
    total_generated: int
    dedup_drop_count: int
    dedup_skip_count: int = 0
    avg_generation_time_ms: float = 0.0
    total_time_ms: float
    model_usage: dict[str, int] = Field(default_factory=dict)


class GenerateRequest(BaseModel):
    project_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    task_domain: str = Field(max_length=200)
    count: int = Field(ge=1, le=200)
    human_likeness: Literal["low", "medium", "high", "insane"]
    source_models: list[str] = Field(default_factory=list)
    similarity_threshold: float | None = None
    extra_params: dict = Field(default_factory=dict)


class GenerateResponse(BaseModel):
    project_id: str
    prompts: list[PromptResponse]
    generation_meta: GenerationMeta


class GenerateAsyncResponse(BaseModel):
    task_id: str
    project_id: str
    status: str


class GenerateProgress(BaseModel):
    task_id: str
    status: str
    progress: float
    completed: int
    total: int
    result: GenerateResponse | None = None


class ErrorDetail(BaseModel):
    loc: list[str] | None = None
    msg: str
    type: str


class ErrorResponse(BaseModel):
    error: dict


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str = "unknown"
    models: dict[str, str] = Field(default_factory=dict)
    embedding: str = "unknown"


ModelConfig = ModelConfigResponse


class ModelConfigInternal(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    provider_type: str
    api_key: str = ""
    base_url: str
    model_name: str
    weight: float
    max_tokens: int
    timeout: int
    scope: str
    project_id: str | None
    enabled: bool
    created_at: datetime
    updated_at: datetime
