from app.core.events.base import EventListener, LevelCompletedEvent
from app.repositories.user import UserRepository
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
        # Заглушка логики достижений
        if event.stars == 3:
            logger.info(
                "[AchievementListener] User %s got 3 stars! Checking 'Perfectionist' achievement...",
                event.user_id,
            )
            # Здесь мы проверили бы/создали логику достижений
