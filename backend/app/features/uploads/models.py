import uuid

from sqlalchemy import Column, DateTime, String, Integer, ForeignKey, Index
from sqlalchemy.sql import func

from app.models.base import Base
from app.models.custom_types import GUID


class Upload(Base):
    __tablename__ = "uploads"
    __table_args__ = (
        Index("ix_uploads_owner_created", "owner_user_id", "created_at"),
        Index("ix_uploads_public_id", "public_id"),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    owner_user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    public_id = Column(String(255), nullable=False, unique=True)
    provider = Column(String(32), nullable=False, default="")

    bytes = Column(Integer, nullable=False, default=0)
    mime = Column(String(128), nullable=True)

    status = Column(String(32), nullable=False, default="uploaded")
    sha256 = Column(String(64), nullable=True)
    error_code = Column(String(64), nullable=True)
    error_detail = Column(String(512), nullable=True)

    access_count = Column(Integer, nullable=False, default=0)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
