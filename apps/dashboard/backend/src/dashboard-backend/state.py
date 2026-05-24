from typing import Set, Dict
from fastapi import WebSocket


class DashboardState:
    def __init__(self):
        self.event_counter: int = 0
        self.active_exporters_count: int = 0
        self.connected_frontends: Set[WebSocket] = set()
        self.exporter_registry: Dict[str, float] = {}
