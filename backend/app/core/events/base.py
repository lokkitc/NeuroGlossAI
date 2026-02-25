from typing import List, Callable, Any, Dict
from dataclasses import dataclass
from uuid import UUID

                 
@dataclass
class Event:
    pass

@dataclass
class LevelCompletedEvent(Event):
    user_id: UUID
    level_id: UUID
    xp_earned: int
    stars: int

                               
class EventListener:
    async def handle(self, event: Event, db: Any = None):
        raise NotImplementedError

                                
class EventBus:
    def __init__(self):
        self._listeners: Dict[str, List[EventListener]] = {}

    def subscribe(self, event_type: type, listener: EventListener):
        event_name = event_type.__name__
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(listener)

    async def publish(self, event: Event, db: Any = None):
        event_name = type(event).__name__
        if event_name in self._listeners:
            for listener in self._listeners[event_name]:
                await listener.handle(event, db)

                                   
event_bus = EventBus()
