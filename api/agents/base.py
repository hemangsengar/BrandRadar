import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class AgentStatus:
    IDLE = "idle"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class BaseAgent(ABC):
    def __init__(self, name: str, on_update: Optional[Callable] = None):
        self.name = name
        self.status = AgentStatus.IDLE
        self.result: Any = None
        self.error: Optional[str] = None
        self.api_calls: dict[str, int] = {}
        self.message: str = "Waiting..."
        self._on_update = on_update

    def update(self, message: str, status: Optional[str] = None):
        self.message = message
        if status:
            self.status = status
        if self._on_update:
            self._on_update(self)
        logger.info(f"[{self.name}] {message}")

    def track_api_call(self, endpoint: str, count: int = 1):
        self.api_calls[endpoint] = self.api_calls.get(endpoint, 0) + count

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        pass

    async def run(self, *args, **kwargs) -> Any:
        self.update(f"Starting {self.name}...", AgentStatus.RUNNING)
        try:
            self.result = await self.execute(*args, **kwargs)
            self.update(f"{self.name} complete.", AgentStatus.COMPLETE)
            return self.result
        except Exception as e:
            self.error = str(e)
            self.update(f"{self.name} failed: {e}", AgentStatus.FAILED)
            raise

    def report(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "api_calls": self.api_calls,
            "error": self.error,
        }
