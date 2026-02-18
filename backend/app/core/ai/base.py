from abc import ABC, abstractmethod
from typing import List, Dict, Any

class LLMProvider(ABC):
    @abstractmethod
    async def generate_json(self, prompt: str, *, temperature: float | None = None) -> Dict[str, Any]:
        """Генерация JSON ответа от LLM"""
        pass

    @abstractmethod
    async def generate_text(self, prompt: str, *, temperature: float | None = None) -> str:
        """Генерация текстового ответа от LLM"""
        pass

    @abstractmethod
    async def generate_chat(self, messages: List[Dict[str, str]], *, temperature: float | None = None) -> str:
        """Генерация чатового ответа от LLM на основе истории сообщений"""
        pass
