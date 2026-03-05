import uuid
from enum import Enum

from sqlalchemy import Column, DateTime, String, ForeignKey
from sqlalchemy.sql import func

from app.models.base import Base
from app.models.custom_types import GUID


class SubscriptionStatus(str, Enum):
    active = "active"
    canceled = "canceled"
    expired = "expired"
    inactive = "inactive"
    superseded = "superseded"


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    tier = Column(String, nullable=False, default="free")
    status = Column(String, nullable=False, default=SubscriptionStatus.active.value)

    started_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    provider = Column(String, nullable=True)
    external_customer_id = Column(String, nullable=True)
    external_subscription_id = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
