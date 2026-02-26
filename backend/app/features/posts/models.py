import uuid

from sqlalchemy import Column, DateTime, String, Boolean, JSON, ForeignKey, Text, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base
from app.models.custom_types import GUID


class Post(Base):
    __tablename__ = "posts"
    __table_args__ = (
        Index("ix_posts_public_created", "is_public", "created_at"),
        Index("ix_posts_author_created", "author_user_id", "created_at"),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    author_user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    character_id = Column(GUID, ForeignKey("characters.id", ondelete="SET NULL"), nullable=True)

    title = Column(String, nullable=False, default="")
    content = Column(Text, nullable=False, default="")

    media = Column(JSON, nullable=True)

    is_public = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    author = relationship("User")
    character = relationship("Character")


class PostLike(Base):
    __tablename__ = "post_likes"
    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uq_post_like"),
        Index("ix_post_likes_post_created", "post_id", "created_at"),
        Index("ix_post_likes_user_created", "user_id", "created_at"),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    post_id = Column(GUID, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    post = relationship("Post")
    user = relationship("User")
