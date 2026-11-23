from abc import ABC, abstractmethod
from pathlib import Path


class BaseAIEngine(ABC):
    """Abstract base class for all AI coding engines."""

    @abstractmethod
    async def ask(self, prompt: str, project_path: Path) -> str:
        """
        Read-only analysis mode: inspects code and returns an answer
        without modifying any files.
        """
        pass

    @abstractmethod
    async def ask_general(self, prompt: str) -> str:
        """
        General question mode: answers questions directly without any
        project directory context (e.g. algorithms, architecture, general knowledge).
        """
        pass

    @abstractmethod
    async def execute(self, prompt: str, project_path: Path) -> str:
        """
        Modification mode: instructs the AI to apply code changes
        in the target project directory.
        """
        pass
