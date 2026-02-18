"""Шаблоны промптов для AI-генерации."""

LESSON_SYSTEM_TEMPLATE = """You are an expert language teacher creating content for language learners.
Generate content that is educational, engaging, and appropriate for the specified level."""

LESSON_TEXT_VOCAB_TEMPLATE = """Generate a language lesson text and vocabulary for {target_language} learners.

Topic: {topic}
Level: {level}
Native language: {native_language}
Student interests: {interests}

Requirements:
1. Create a 150-200 word text in {target_language} strictly about the topic.
2. Stay on-topic. Do not switch to a generic or unrelated topic.
3. Use only {target_language} in the lesson text. Do not include any {native_language} or English words.
4. Include 6-8 vocabulary words that actually appear in the text.
5. For each vocabulary item provide:
   - word in {target_language}
   - translation in {native_language}
   - context sentence in {target_language}

Hard rules:
- The lesson text must reflect the topic. If the topic is game-related (e.g., Mobile Legends), the text must mention game concepts (players, match, roles, team, items, map, etc.) in {target_language}.
- Do not talk about "alphabet", "letters", or pronunciation unless the topic explicitly asks for it.
- Output must be valid JSON only. No markdown. No extra keys.

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

LESSON_EXERCISES_TEMPLATE = """Generate 4-5 varied exercises based on this {target_language} lesson.

Language rules (very important):
- quiz.question MUST be only in {target_language}.
- quiz.options MUST be only in {target_language}. Avoid single-word options that could be mistaken for another language; prefer short phrases (2-5 words) or numerals where appropriate.
- true_false.statement MUST be only in {target_language} (no translations in quotes, no bilingual text).
- fill_blank.sentence MUST be only in {target_language}.
- scramble.correct_sentence MUST be only in {target_language}.
- match.pairs.left MUST be only in {target_language}.
- match.pairs.right MUST be only in {native_language} (translations only).
- Do not include English words anywhere.

Text: {text}
Vocabulary pairs:
{vocab_pairs}

Create exercises of these types:
- quiz (multiple choice question with 4 options, correct_index 0-3)
- match (pairs to connect left/right)
- true_false (statement with is_true boolean)
- fill_blank (sentence with ___ placeholder, correct_word, blank_index, full_sentence_native)
- scramble (scrambled_parts array, correct_sentence)

Quality check before output:
- Verify every field follows the language rules above.
- Every exercise must be solvable using ONLY the provided Text and Vocabulary pairs.

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
      "blank_index": 0,
      "full_sentence_native": "full correct sentence in native language without blanks"
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
Theme: {theme}
Interests: {interests}

Create a structured course with 3-4 sections, each containing 3-4 units.

Hard rules:
- The course MUST be themed. Every section title and every unit topic/description MUST clearly relate to Theme: {theme}.
- Do NOT generate generic units unrelated to the theme (e.g., unrelated school topics) unless the theme explicitly asks for it.
- If the theme is a game (e.g., Mobile Legends), incorporate real in-game contexts: roles, lanes, map locations, items, abilities, team communication, match phases, strategy talk.
- Output must be valid JSON only. No markdown. No extra keys.

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
