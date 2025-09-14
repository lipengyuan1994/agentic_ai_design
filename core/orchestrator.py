from abc import ABC, abstractmethod

class Orchestrator(ABC):
    """Base class for all orchestrators."""

    @abstractmethod
    def run(self, *args, **kwargs):
        """Runs the orchestrator."""
        pass
