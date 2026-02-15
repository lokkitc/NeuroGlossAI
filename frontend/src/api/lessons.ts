import { apiRequest } from './apiClient'

export type GeneratedVocabularyItem = {
  id: string
  user_lexeme_id?: string | null
  word?: string | null
  translation?: string | null
  context_sentence?: string | null
}

// Типы упражнений, как с бэкенда
export type Exercise =
  | QuizExercise
  | MatchExercise
  | TrueFalseExercise
  | FillBlankExercise
  | ScrambleExercise

export interface QuizExercise {
  type: 'quiz'
  question: string
  options: string[]
  correct_index: number
}

export interface MatchExercise {
  type: 'match'
  pairs: Array<{ left: string; right: string }>
}

export interface TrueFalseExercise {
  type: 'true_false'
  statement: string
  is_true: boolean
}

export interface FillBlankExercise {
  type: 'fill_blank'
  sentence: string
  correct_word: string
}

export interface ScrambleExercise {
  type: 'scramble'
  scrambled_parts: string[]
  correct_sentence: string
}

export type GeneratedLesson = {
  id: string
  enrollment_id: string
  level_template_id: string
  topic_snapshot?: string | null
  content_text: string
  exercises?: Exercise[] | null
  quality_status: string
  created_at: string
  vocabulary_items: GeneratedVocabularyItem[]
}

export type GenerateLessonRequest = {
  level_template_id: string
  topic: string
  level?: string
  generation_mode?: string
}

export const lessonsApi = {
  list: (params?: { skip?: number; limit?: number }) => {
    const q = new URLSearchParams()
    if (params?.skip !== undefined) q.set('skip', String(params.skip))
    if (params?.limit !== undefined) q.set('limit', String(params.limit))
    const suffix = q.toString() ? `?${q.toString()}` : ''
    return apiRequest<GeneratedLesson[]>({ path: `/lessons${suffix}`, method: 'GET' })
  },
  getById: (id: string) => apiRequest<GeneratedLesson>({ path: `/lessons/${id}`, method: 'GET' }),
  generate: (body: GenerateLessonRequest) =>
    apiRequest<GeneratedLesson>({ path: '/lessons/generate', method: 'POST', body }),
  regenExercises: (id: string) =>
    apiRequest<GeneratedLesson>({ path: `/lessons/${id}/regen-exercises`, method: 'POST' }),
  regenCore: (id: string, body?: { level?: string; generation_mode?: string }) =>
    apiRequest<GeneratedLesson>({
      path: `/lessons/${id}/regen-core`,
      method: 'POST',
      body: body ?? {},
    }),
}
