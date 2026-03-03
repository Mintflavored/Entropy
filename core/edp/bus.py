"""
EDP Bus — реактивная шина доставки данных.
Компоненты подписываются на типы данных, Bus доставляет обновления.
"""

import logging
from collections import defaultdict
from typing import Any, Callable

logger = logging.getLogger(__name__)


class EDPBus:
    """Реактивная шина: subscribe/publish по типам данных."""

    def __init__(self):
        # {type_name: [callback, ...]}
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event_type: type, callback: Callable):
        """Подписаться на тип данных."""
        type_name = event_type.__name__
        self._subscribers[type_name].append(callback)
        logger.debug(f"EDP Bus: subscribed to {type_name}")

    def publish(self, event: Any):
        """Отправить событие всем подписчикам соответствующего типа."""
        type_name = type(event).__name__
        subscribers = self._subscribers.get(type_name, [])

        for callback in subscribers:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"EDP Bus delivery error ({type_name}): {e}")

    def publish_many(self, events: list):
        """Отправить список событий."""
        for event in events:
            self.publish(event)

    @property
    def subscriber_count(self) -> int:
        """Общее количество подписок."""
        return sum(len(subs) for subs in self._subscribers.values())
