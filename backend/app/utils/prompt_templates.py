"""Шаблоны промптов для AI-генерации."""

LESSON_SYSTEM_TEMPLATE = """You are an expert language teacher creating content for language learners.
Generate content that is educational, engaging, and appropriate for the specified level."""

LESSON_TEXT_ONLY_TEMPLATE = """Generate ONLY a language lesson text for {target_language} learners.

COURSE UNIT TOPIC / LESSON THEME: {topic}
Level: {level}
Native language: {native_language}
Student interests: {interests}

Requirements:
1. Create a 150-200 word text in {target_language} strictly about the topic.
2. Use only {target_language} in the text. Do not include any {native_language} or English words.
3. Stay on-topic. Do not switch to a generic or unrelated topic.

Content requirements (make it informative, not generic):
- Explain the key idea of the topic in simple A1 sentences.
- If the topic is a GAME ROLE topic (marksman/fighter/etc.), include practical game context:
  - what the role does
  - where the role usually plays (lane/position)
  - what to do early vs late
  - 1-2 common mistakes to avoid

Topic disambiguation (IMPORTANT):
- If the topic mentions Mobile Legends, MOBA, heroes, roles like marksman/fighter/tank/mage/support/assassin, it MUST be about the VIDEO GAME context (match, team, roles, map, items, skills).
- Do NOT write about real-world warriors, history, war, or heroic deeds unless the topic explicitly asks for real history.

Entity rules (IMPORTANT):
- Do NOT invent character/hero names.
- If the topic provides specific real names/entities, you may use ONLY those.
- If VERIFIED TOPIC CONTEXT provides a verified roster/entities list, you may use ONLY names from that list.
- Otherwise, write using generic role terms (e.g., "marksman", "fighter", "the player", "the team") without naming specific heroes.

Hard rules:
- Output must be valid JSON only. No markdown. No extra keys.

Output JSON format:
{{
  "text": "lesson text in target language"
}}"""


CHAT_LEARNING_LESSON_TEMPLATE = """Create a mini-lesson from the following chat. Focus ONLY on vocabulary/phrases that appeared in the chat. Do not correct the user, do not grade. Keep it fun and grounded in the conversation.
CRITICAL: Do NOT invent phrases, examples, or facts that are not present in the chat.
Every vocabulary item MUST include an exact quote from the chat where it appears.
Every exercise MUST include an exact sentence_source substring copied from the chat.
Output ONLY valid JSON with keys: title, topic, text, vocabulary, exercises.

JSON schema:
{{
  "title": string,
  "topic": string,
  "text": string,
  "vocabulary": [
    {{"phrase": string, "meaning": string, "source_quote": string, "example_quote": string}}
  ],
  "exercises": [
    {{"type": "quiz"|"match"|"fill_blank"|"scramble", "sentence_source": string, "targets": [string], ...}}
  ]
}}

Rules:
- vocabulary items must be phrases or words that appeared verbatim in the chat
- 6-10 vocabulary items
- source_quote and example_quote MUST be exact substrings from the chat
- exercises must be solvable using only the chat and the vocabulary list
- sentence_source MUST be an exact substring from the chat

CHAT:
{chat}
"""


CHAT_SESSION_SUMMARY_TEMPLATE = """Summarize the conversation so far into a compact, factual memory that helps continue the story. Keep names, relationships, goals, conflicts, and any promises. Do not add new facts.
Output plain text only.

PREVIOUS SUMMARY (may be empty):
{previous_summary}

NEW DIALOGUE:
{dialogue}
"""


ROOM_CHAT_TURN_JSON_TEMPLATE = """You are generating the next multi-character turn. Follow the SYSTEM rules below.

{transcript}

IMPORTANT: Output ONLY valid JSON: {{"speaker": string, "message": string}}.
"""


VOCAB_FROM_TEXT_TEMPLATE = """Extract vocabulary for a {target_language} lesson text.

Native language: {native_language}
Level: {level}

Text:
{text}

Requirements:
1. Select 6-8 important words/phrases that actually appear in the text.
2. For each vocabulary item provide:
   - word in {target_language} (must appear verbatim in the text)
   - translation in {native_language}
   - context sentence in {target_language}

Hard rules:
- Output must be valid JSON only. No markdown. No extra keys.

Output JSON format:
{{
  "vocabulary": [
    {{
      "word": "target language word",
      "translation": "native language translation",
      "context": "sentence using the word in target language"
    }}
  ]
}}"""

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

Content requirements (make it informative, not generic):
- Explain the key idea of the topic in simple A1 sentences.
- If the topic is a GAME ROLE topic (marksman/fighter/etc.), include practical game context:
  - what the role does
  - where the role usually plays (lane/position)
  - what to do early vs late
  - 1-2 common mistakes to avoid

Hard rules:
- The lesson text must reflect the topic. If the topic is game-related (e.g., Mobile Legends), the text must mention game concepts (players, match, roles, team, items, map, etc.) in {target_language}.
- If the topic mentions heroes/roles (marksman/fighter/etc.), interpret them as GAME ROLES (MOBA), not real-world warriors.
- Do NOT invent hero/character names. Use only names explicitly provided in the topic OR present in VERIFIED TOPIC CONTEXT roster/entities, otherwise keep it generic (roles, team, match).
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


VOCAB_EXERCISES_TEMPLATE = """Generate ONLY vocabulary-based exercises for a {target_language} lesson.

COURSE UNIT TOPIC / LESSON THEME:
{topic}

Native language: {native_language}

Vocabulary pairs:
{vocab_pairs}

Rules:
- Output must be valid JSON only. No markdown. No extra keys.
- Every exercise MUST be solvable using ONLY the vocabulary pairs.
- No English words.
- Do NOT invent any named entities (heroes/characters). Use only terms present in the vocabulary pairs.
- Include traceability fields:
  - source: must be "vocab"
  - targets: list of vocabulary words used by the exercise

Create exercises of these types:
- quiz (question+options in {target_language}, correct_index)
- match (pairs.left in {target_language}, pairs.right in {native_language})

Output JSON format:
{{
  "exercises": [
    {{
      "type": "quiz",
      "source": "vocab",
      "targets": ["word1"],
      "question": "...",
      "options": ["...", "...", "...", "..."],
      "correct_index": 0
    }},
    {{
      "type": "match",
      "source": "vocab",
      "targets": ["word1", "word2"],
      "pairs": [
        {{"left": "...", "right": "..."}}
      ]
    }}
  ]
}}"""


TEXT_EXERCISES_TEMPLATE = """Generate ONLY text-based exercises for a {target_language} lesson.

COURSE UNIT TOPIC / LESSON THEME:
{topic}

Native language: {native_language}

Text:
{text}

Vocabulary pairs:
{vocab_pairs}

Rules:
- Output must be valid JSON only. No markdown. No extra keys.
- Exercises MUST be solvable using ONLY the provided Text and Vocabulary pairs.
- No English words.
- Do NOT invent any named entities (heroes/characters). Use only what exists in the provided Text/Vocabulary pairs.
- Include traceability fields:
  - source: must be "text"
  - targets: list of vocabulary words used by the exercise

Create exercises of these types:
- true_false
- fill_blank
- scramble

For EVERY exercise add:
- sentence_source: an EXACT substring copied from the provided Text that the exercise is based on.

Output JSON format:
{{
  "exercises": [
    {{
      "type": "true_false",
      "source": "text",
      "targets": ["word1"],
      "sentence_source": "...",
      "statement": "...",
      "is_true": true
    }},
    {{
      "type": "fill_blank",
      "source": "text",
      "targets": ["word1"],
      "sentence_source": "...",
      "sentence": "... ___ ...",
      "correct_word": "...",
      "blank_index": 0,
      "full_sentence_native": "..."
    }},
    {{
      "type": "scramble",
      "source": "text",
      "targets": ["word1"],
      "sentence_source": "...",
      "scrambled_parts": ["..."],
      "correct_sentence": "..."
    }}
  ]
}}"""


LESSON_PLAN_TEMPLATE = """You are an expert language teacher.

Create a SHORT plan for a {target_language} lesson. Native language is {native_language}. Level: {level}.
Topic: {topic}
Student interests: {interests}

Hard rules:
- Output must be valid JSON only. No markdown. No extra keys.
- Keep plan concise.
- Avoid repeating topics from prior lessons.

Already covered topics:
{prior_topics}

Already used vocabulary (avoid using these as target words):
{used_words}

Output JSON format:
{{
  "topic": "...",
  "goal": "...",
  "key_points": ["...", "...", "..."],
  "vocab_targets": ["...", "...", "..."],
  "grammar_focus": "...",
  "avoid_list": ["..."]
}}"""


LESSON_REVIEW_TEMPLATE = """You are a strict QA reviewer for generated language lessons.

You will be given a JSON object with keys: text, vocabulary.
Target language: {target_language}
Native language: {native_language}
Topic: {topic}
Level: {level}

Check for:
- Lesson text contains non-{target_language} words.
- Vocabulary words do not appear in the text.
- Translation is not in {native_language}.
- Context sentences are not in {target_language}.
- Off-topic content.
- Too short/too long (150-200 words target).

Output must be valid JSON only.

Output JSON format:
{{
  "issues": [
    {{"code": "...", "field": "...", "why": "...", "fix_hint": "..."}}
  ]
}}"""


EXERCISES_REVIEW_TEMPLATE = """You are a strict QA reviewer for generated lesson exercises.

Target language: {target_language}
Native language: {native_language}

You will be given exercises JSON. Check:
- Language rules per exercise type (target vs native language fields).
- Exercises solvable using only the provided text and vocabulary pairs.
- No English words.

Output must be valid JSON only.

Output JSON format:
{{
  "issues": [
    {{"code": "...", "field": "...", "why": "...", "fix_hint": "..."}}
  ]
}}"""

LESSON_EXERCISES_TEMPLATE = """Generate 4-5 varied exercises based on this {target_language} lesson.

COURSE UNIT TOPIC / LESSON THEME:
{topic}

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
- Do NOT invent any named entities (heroes/characters). Use only what exists in the provided Text/Vocabulary pairs.

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
