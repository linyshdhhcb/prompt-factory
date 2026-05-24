from datetime import datetime

from sqlalchemy import JSON, CheckConstraint, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class PersonaTrait(Base):
    __tablename__ = "persona_traits"
    __table_args__ = (
        CheckConstraint("scope IN ('public', 'project')", name="ck_persona_traits_scope"),
        Index("ix_persona_traits_category", "category"),
        Index("ix_persona_traits_scope_project", "scope", "project_id"),
        Index("ix_persona_traits_project_scope_project", "project_id", postgresql_where="scope = 'project'"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    traits: Mapped[list] = mapped_column(JSON, default=list)
    weight: Mapped[float] = mapped_column(default=1.0)
    scope: Mapped[str] = mapped_column(String(20), nullable=False, default="public")
    project_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)
