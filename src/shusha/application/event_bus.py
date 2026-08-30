"""Synchronous in-memory Event Bus for typed domain and application events."""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any, TypeVar

from shusha.domain.events import DomainEvent

T = TypeVar("T", bound=DomainEvent)
EventHandler = Callable[[T], None]

logger = logging.getLogger(__name__)


class EventBus:
    """Publish-subscribe event bus decoupling producers from consumers."""

    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[EventHandler[Any]]] = defaultdict(
            list
        )
        self._global_handlers: list[EventHandler[DomainEvent]] = []

    def subscribe(
        self, event_type: type[T], handler: Callable[[T], None]
    ) -> Callable[[], None]:
        """Subscribe a handler to a specific event type. Returns an unsubscribe function."""
        self._handlers[event_type].append(handler)  # type: ignore[arg-type]

        def unsubscribe() -> None:
            if handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)  # type: ignore[arg-type]

        return unsubscribe

    def subscribe_all(
        self, handler: Callable[[DomainEvent], None]
    ) -> Callable[[], None]:
        """Subscribe a handler to all published domain events."""
        self._global_handlers.append(handler)

        def unsubscribe() -> None:
            if handler in self._global_handlers:
                self._global_handlers.remove(handler)

        return unsubscribe

    def publish(self, event: DomainEvent) -> None:
        """Dispatch event to all matching type-specific and global handlers."""
        # 1. Type-specific handlers
        for handler in list(self._handlers.get(type(event), [])):
            try:
                handler(event)
            except Exception as e:
                logger.exception("Error executing event handler %s: %s", handler, e)

        # 2. Global handlers
        for global_handler in list(self._global_handlers):
            try:
                global_handler(event)
            except Exception as e:
                logger.exception(
                    "Error executing global event handler %s: %s", global_handler, e
                )

    def clear(self) -> None:
        """Remove all registered subscriptions."""
        self._handlers.clear()
        self._global_handlers.clear()

    def subscriber_count(self, event_type: type[DomainEvent] | None = None) -> int:
        """Return count of registered subscribers for an event type or total."""
        if event_type is not None:
            return len(self._handlers.get(event_type, []))
        return sum(len(h) for h in self._handlers.values()) + len(self._global_handlers)
