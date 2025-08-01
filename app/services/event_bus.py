from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Callable, Dict, Iterable, List

from app.schemas.events import DomainEvent

EventHandler = Callable[[DomainEvent], None]


class EventBus:
    """Simple in-memory event bus for pub/sub style notifications."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[EventHandler]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        if handler not in self._subscribers[event_name]:
            self._subscribers[event_name].append(handler)

    def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        if handler in self._subscribers.get(event_name, []):
            self._subscribers[event_name].remove(handler)

    def publish(self, event_name: str, payload: Dict[str, Any]) -> DomainEvent:
        event = DomainEvent(name=event_name, payload=payload, occurred_at=datetime.utcnow())
        for handler in list(self._subscribers.get(event_name, [])):
            handler(event)
        return event

    def subscribers(self, event_name: str) -> Iterable[EventHandler]:
        return tuple(self._subscribers.get(event_name, []))
