"""Шаблоны промптов для AI-генерации."""

LESSON_SYSTEM_TEMPLATE = """You are an expert language teacher creating content for language learners.
Generate content that is educational, engaging, and appropriate for the specified level."""

LESSON_TEXT_VOCAB_TEMPLATE = """Generate a language lesson text and vocabulary for {target_language} learners.

Topic: {topic}
Level: {level}
Native language: {native_language}
Student interests: {interests}

Requirements:
1. Create a 150-200 word text in {target_language} about the topic
2. Include 6-8 vocabulary words from the text
3. For each vocabulary item provide:
   - word in {target_language}
   - translation in {native_language}
   - context sentence in {target_language}

Output JSON format:
{{
  "text": "lesson text in target language",
  "vocabulary": [
    {{
      "word": "target language word",
      "translation": "native language translation",
      "context": "sentence using the word in target language"
    }}
  ]
}}"""

LESSON_EXERCISES_TEMPLATE = """Generate 4-5 varied exercises based on this {target_language} lesson:

Text: {text}
Vocabulary pairs:
{vocab_pairs}

Create exercises of these types:
- quiz (multiple choice question with 4 options, correct_index 0-3)
- match (pairs to connect left/right)
- true_false (statement with is_true boolean)
- fill_blank (sentence with ___ placeholder, correct_word, blank_index)
- scramble (scrambled_parts array, correct_sentence)

Output JSON format:
{{
  "exercises": [
    {{
      "type": "quiz",
      "question": "question text",
      "options": ["option1", "option2", "option3", "option4"],
      "correct_index": 0
    }},
    {{
      "type": "match",
      "pairs": [
        {{"left": "item1", "right": "match1"}},
        {{"left": "item2", "right": "match2"}}
      ]
    }},
    {{
      "type": "true_false",
      "statement": "statement text",
      "is_true": true
    }},
    {{
      "type": "fill_blank",
      "sentence": "sentence with ___ placeholder",
      "correct_word": "missing word",
      "blank_index": 0
    }},
    {{
      "type": "scramble",
      "scrambled_parts": ["part1", "part2", "part3"],
      "correct_sentence": "correct sentence"
    }}
  ]
}}"""

ROLEPLAY_SYSTEM_TEMPLATE = """You are a language practice assistant for {target_language} learners.
Role: {role}
Scenario: {scenario}
Level: {level}

Guidelines:
- Respond in {target_language} appropriate for {level} level
- Stay in character as {role}
- Help the user practice the scenario
- Be encouraging and provide corrections when needed
- Keep responses conversational and natural"""

PATH_GENERATION_TEMPLATE = """Generate a learning path for {target_language} speakers who know {native_language}.

Level: {level}
Interests: {interests}

Create a structured course with 3-4 sections, each containing 3-4 units.

Output JSON format:
{{
  "sections": [
    {{
      "order": 1,
      "title": "section title",
      "description": "section description",
      "units": [
        {{
          "order": 1,
          "topic": "unit topic",
          "description": "unit description",
          "icon": "emoji icon"
        }}
      ]
    }}
  ]
}}"""
