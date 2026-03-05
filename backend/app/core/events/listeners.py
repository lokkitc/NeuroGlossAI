from app.core.events.base import EventListener, LevelCompletedEvent
from app.features.users.repository import UserRepository
from app.features.achievements.service import AchievementService
import logging

logger = logging.getLogger(__name__)

class XPListener(EventListener):
    async def handle(self, event: LevelCompletedEvent, db):
        logger.info("[XPListener] Adding %s XP to user %s", event.xp_earned, event.user_id)
        user_repo = UserRepository(db)
        user = await user_repo.get(event.user_id)
        if user:
            user.xp += event.xp_earned
            await user_repo.update(user, {"xp": user.xp})


class AchievementListener(EventListener):
    async def handle(self, event: LevelCompletedEvent, db):
        try:
            if int(getattr(event, "stars", 0) or 0) != 3:
                return
            await AchievementService(db).award(
                user_id=event.user_id,
                slug="perfectionist_3stars",
                context={
                    "level_id": str(event.level_id),
                    "stars": int(event.stars),
                },
            )
        except Exception:
            logger.exception("[AchievementListener] Failed to award achievement")
