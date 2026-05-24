from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class MetaPromptTemplate(Base):
    __tablename__ = "meta_prompt_templates"
    __table_args__ = (
        CheckConstraint("scope IN ('public', 'project')", name="ck_meta_prompt_templates_scope"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    template: Mapped[str] = mapped_column(Text, nullable=False)
    scope: Mapped[str] = mapped_column(String(20), nullable=False, default="public")
    project_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    weight: Mapped[float] = mapped_column(default=1.0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
