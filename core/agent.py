from abc import ABC, abstractmethod

class Agent(ABC):
    """Abstract base class for all agents."""

    @abstractmethod
    def run(self, *args, **kwargs):
        """Run the agent."""
        pass
