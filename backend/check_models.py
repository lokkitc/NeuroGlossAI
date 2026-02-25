"""Утилита для проверки доступных моделей внешнего провайдера.

Скрипт исторический (Gemini) и не используется в основном runtime.
"""

import httpx
import asyncio
import os
import sys

                                                                                
sys.path.append(os.getcwd())

from app.core.config import settings

async def list_models():
    api_key = settings.GEMINI_API_KEY
    print(f"Проверяем ключ: {api_key[:5]}...")
    
    if not api_key:
        print("API key не найден!")
        return

    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            print(f"Статус: {response.status_code}")
            if response.status_code == 200:
                models = response.json().get("models", [])
                print("\nДоступные модели для generateContent:")
                found = False
                for m in models:
                    if "generateContent" in m.get("supportedGenerationMethods", []):
                        print(f" - {m['name']}")
                        found = True
                if not found:
                    print("Не найдено моделей, поддерживающих generateContent.")
            else:
                print(f"Ошибка: {response.text}")
        except Exception as e:
            print(f"Исключение: {e}")

if __name__ == "__main__":
    asyncio.run(list_models())
