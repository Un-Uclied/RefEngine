"""Simple pub/sub event bus for game-wide notifications."""
from collections import defaultdict
from typing import Callable, Any


class EventBus:
    def __init__(self):
        # mapping event name -> list of callables
        self._listeners: dict[str, list[Callable[..., Any]]] = defaultdict(list)

    def subscribe(self, event: str, callback: Callable[..., Any]) -> None:
        """Register *callback* to be invoked when *event* is published."""
        self._listeners[event].append(callback)

    def unsubscribe(self, event: str, callback: Callable[..., Any]) -> None:
        """Remove a previously-registered listener."""
        if event in self._listeners:
            try:
                self._listeners[event].remove(callback)
            except ValueError:
                pass

    def publish(self, event: str, **kwargs: Any) -> None:
        """Notify all listeners of *event*, passing keyword args."""
        for cb in list(self._listeners.get(event, [])):
            try:
                cb(**kwargs)
            except Exception as e:
                print(f"EventBus listener error on '{event}': {e}")


# a single global bus that modules can import
bus = EventBus()