from typing import Dict, Any, Tuple, List
import uuid
from app.models.generated_content import GeneratedLesson, GeneratedVocabularyItem
from app.models.enrollment import Enrollment


class GeneratedLessonFactory:
    @staticmethod
    def create_from_ai_response(
        ai_data: Dict[str, Any],
        enrollment: Enrollment,
        level_template_id: uuid.UUID,
        topic: str,
        prompt_version: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        input_context: Dict[str, Any] | None = None,
        raw_model_output: Dict[str, Any] | None = None,
        validation_errors: Any | None = None,
        repair_count: int = 0,
        quality_status: str = "ok",
    ) -> Tuple[GeneratedLesson, List[GeneratedVocabularyItem]]:
        lesson = GeneratedLesson(
            enrollment_id=enrollment.id,
            level_template_id=level_template_id,
            topic_snapshot=topic,
            prompt_version=prompt_version,
            provider=provider,
            model=model,
            input_context=input_context,
            raw_model_output=raw_model_output,
            validation_errors=validation_errors,
            repair_count=repair_count,
            content_text=ai_data.get("text", ""),
            exercises=ai_data.get("exercises", []),
            quality_status=quality_status,
        )

        vocab_items: list[GeneratedVocabularyItem] = []
        for item in ai_data.get("vocabulary", []):
            vocab_items.append(
                GeneratedVocabularyItem(
                    generated_lesson_id=lesson.id,
                    word=item.get("word"),
                    translation=item.get("translation"),
                    context_sentence=item.get("context"),
                )
            )

        return lesson, vocab_items
