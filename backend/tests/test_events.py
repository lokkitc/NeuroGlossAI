"""Тесты событийной шины и базовых слушателей.

Проверяем подписку/публикацию и обновление XP через XPListener.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.core.events.base import EventBus, LevelCompletedEvent
from app.core.events.listeners import XPListener
from app.repositories.user import UserRepository

@pytest.mark.asyncio
async def test_event_bus_publish_subscribe():
                
    bus = EventBus()
    mock_listener = AsyncMock()
    mock_listener.handle = AsyncMock()
    
              
    bus.subscribe(LevelCompletedEvent, mock_listener)
    
                
    event = LevelCompletedEvent(user_id="u1", level_id="l1", xp_earned=100, stars=3)
    await bus.publish(event, db=None)
    
              
    mock_listener.handle.assert_called_once_with(event, None)

@pytest.mark.asyncio
async def test_xp_listener_updates_user():
                
    listener = XPListener()
    mock_db = MagicMock()
    
                                      
                                                                                                

                                
    mock_user = MagicMock()
    mock_user.xp = 50
    
                                                   
    mock_result = MagicMock()
    mock_result.scalars().first.return_value = mock_user
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    
             
    event = LevelCompletedEvent(user_id="u1", level_id="l1", xp_earned=100, stars=3)
    
                
    await listener.handle(event, mock_db)
    
              
    assert mock_user.xp == 150            
    mock_db.commit.assert_called()
