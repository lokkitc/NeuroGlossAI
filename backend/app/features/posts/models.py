import uuid

from sqlalchemy import Column, DateTime, String, Boolean, JSON, ForeignKey, Text, UniqueConstraint, Index, Integer
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

    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    like_count = Column(Integer, nullable=False, default=0)
    comment_count = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    author = relationship("User")
    character = relationship("Character")

    comments = relationship(
        "PostComment",
        cascade="all, delete-orphan",
        order_by="PostComment.created_at.asc()",
    )


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


class PostComment(Base):
    __tablename__ = "post_comments"
    __table_args__ = (
        Index("ix_post_comments_post_created", "post_id", "created_at"),
        Index("ix_post_comments_author_created", "author_user_id", "created_at"),
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    post_id = Column(GUID, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    author_user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    parent_id = Column(GUID, ForeignKey("post_comments.id", ondelete="SET NULL"), nullable=True)

    content = Column(Text, nullable=False, default="")

    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    post = relationship("Post")
    author = relationship("User")
    parent = relationship("PostComment", remote_side=[id])
