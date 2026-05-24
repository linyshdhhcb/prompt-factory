from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ModelConfig(Base):
    __tablename__ = "model_configs"
    __table_args__ = (
        CheckConstraint("scope IN ('public', 'project')", name="ck_model_configs_scope"),
        CheckConstraint(
            "provider_type IN ('openai', 'anthropic', 'azure', 'bedrock')",
            name="ck_model_configs_provider_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    provider_type: Mapped[str] = mapped_column(String(20), nullable=False, default="openai")
    api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    weight: Mapped[float] = mapped_column(default=1.0)
    max_tokens: Mapped[int] = mapped_column(Integer, default=256)
    timeout: Mapped[int] = mapped_column(Integer, default=30)
    scope: Mapped[str] = mapped_column(String(20), nullable=False, default="public")
    project_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)
