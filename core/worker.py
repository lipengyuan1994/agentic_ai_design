from abc import ABC, abstractmethod

class Worker(ABC):
    """Base class for all worker agents."""

    @abstractmethod
    def run(self, *args, **kwargs):
        """Runs the worker agent."""
        pass
