from abc import ABC, abstractmethod
from typing import List, Dict, Any

class LLMProvider(ABC):
    @abstractmethod
    async def generate_json(self, prompt: str) -> Dict[str, Any]:
        """Generate a JSON response from the LLM."""
        pass

    @abstractmethod
    async def generate_text(self, prompt: str) -> str:
        """Generate a text response from the LLM."""
        pass

    @abstractmethod
    async def generate_chat(self, messages: List[Dict[str, str]]) -> str:
        """Generate a chat response from the LLM based on a message history."""
        pass
