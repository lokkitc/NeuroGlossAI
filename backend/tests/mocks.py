"""Моки LLM-провайдера для тестов.

Возвращает детерминированные JSON ответы для генерации курса и уроков.
"""

from typing import List, Dict, Any
from app.core.ai.base import LLMProvider

class MockLLMProvider(LLMProvider):
    async def generate_json(self, prompt: str) -> Dict[str, Any]:
                                                             
        if "Create a mini-lesson from the following chat" in prompt and "source_quote" in prompt and "sentence_source" in prompt:
            return {
                "title": "Chat Mini Lesson",
                "topic": "Conversation",
                "text": "Mini lesson based on the chat.",
                "vocabulary": [
                    {
                        "phrase": "apple",
                        "meaning": "яблоко",
                        "source_quote": "I bought an apple.",
                        "example_quote": "I bought an apple.",
                    },
                    {
                        "phrase": "coffee",
                        "meaning": "кофе",
                        "source_quote": "I need coffee.",
                        "example_quote": "I need coffee.",
                    },
                    {
                        "phrase": "music",
                        "meaning": "музыка",
                        "source_quote": "I like music.",
                        "example_quote": "I like music.",
                    },
                    {
                        "phrase": "book",
                        "meaning": "книга",
                        "source_quote": "This book is good.",
                        "example_quote": "This book is good.",
                    },
                    {
                        "phrase": "park",
                        "meaning": "парк",
                        "source_quote": "We walked in the park.",
                        "example_quote": "We walked in the park.",
                    },
                    {
                        "phrase": "tomorrow",
                        "meaning": "завтра",
                        "source_quote": "See you tomorrow.",
                        "example_quote": "See you tomorrow.",
                    },
                ],
                "exercises": [
                    {
                        "type": "fill_blank",
                        "sentence_source": "I bought an apple.",
                        "targets": ["apple"],
                        "sentence": "I bought an ___.",
                        "correct": "apple",
                    }
                ],
            }

        if "expert curriculum designer" in prompt:
             return {
                "sections": [
                    {
                        "order": 1,
                        "title": "Mobile Legends Basics",
                        "description": "Introduction to the battlefield",
                        "units": [
                            {"order": 1, "topic": "Laning Phase", "description": "How to farm", "icon": "🌾"},
                            {"order": 2, "topic": "Jungle Rotation", "description": "Ganking lanes", "icon": "🐅"}
                        ]
                    }
                ]
            }

                                                                                    
        if "for Kazakh" in prompt or "Language: Kazakh" in prompt or "{target_language}" in prompt:
            return {
                "text": "Mobile Legends — бұл МОБА ойыны. Сен батырды таңдайсың және командамен ойнайсың. Мақсат — қарсыластың базасын бұзу.",
                "vocabulary": [
                    {"word": "батыр", "translation": "Герой", "context": "Мен батырды таңдаймын."},
                    {"word": "база", "translation": "База", "context": "Базаны қорға."},
                    {"word": "команда", "translation": "Команда", "context": "Біз командамен ойнаймыз."},
                    {"word": "ойын", "translation": "Игра", "context": "Бұл қызық ойын."},
                    {"word": "мақсат", "translation": "Цель", "context": "Мақсат анық."},
                    {"word": "қарсылас", "translation": "Противник", "context": "Қарсылас күшті."}
                ],
                "exercises": [
                    {
                        "type": "quiz",
                        "question": "Мақсат қандай?",
                        "options": ["Ұйықтау", "Жеу", "Базаны бұзу"],
                        "correct_index": 2
                    },
                    {
                        "type": "quiz",
                        "question": "Сен нені таңдайсың?",
                        "options": ["Батыр", "Кітап", "Кофе"],
                        "correct_index": 0
                    },
                    {
                        "type": "quiz",
                        "question": "Бұл қандай ойын?",
                        "options": ["МОБА", "Шахмат", "Футбол"],
                        "correct_index": 0
                    },
                    {
                        "type": "match",
                        "pairs": [
                            {"left": "батыр", "right": "Герой"},
                            {"left": "база", "right": "База"},
                            {"left": "команда", "right": "Команда"},
                            {"left": "қарсылас", "right": "Противник"}
                        ]
                    },
                    {
                        "type": "fill_blank",
                        "sentence": "Мақсат — қарсыластың ___ бұзу",
                        "correct_word": "базасын",
                        "full_sentence_native": "Цель — разрушить базу противника"
                    },
                    {
                        "type": "fill_blank",
                        "sentence": "Мен ___ таңдаймын",
                        "correct_word": "батырды",
                        "full_sentence_native": "Я выбираю героя"
                    },
                    {
                        "type": "scramble",
                        "scrambled_parts": ["біз", "ойнаймыз", "командамен"],
                        "correct_sentence": "біз командамен ойнаймыз"
                    }
                ]
            }

                                            
        return {
            "text": "Mobile Legends is a MOBA game. You choose a hero and fight. The goal is to destroy the enemy base.",
            "vocabulary": [
                {"word": "Hero", "translation": "Hero", "context": "Choose your hero wisely."},
                {"word": "Base", "translation": "Base", "context": "Protect your base."}
            ],
            "exercises": [
                {
                    "type": "quiz",
                    "question": "What is the goal?",
                    "options": ["Sleep", "Eat", "Destroy base"],
                    "correct_index": 2
                }
            ]
        }

    async def generate_text(self, prompt: str) -> str:
        return "Mock Text Response"

    async def generate_chat(self, messages: List[Dict[str, str]]) -> str:
        return "I am Layla, the energy gunner! Let's go!"
