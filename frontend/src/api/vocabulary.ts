import { apiRequest } from './apiClient'

export type VocabularyItem = {
  id: string
  word: string
  translation: string
  context_sentence: string
  mastery_level: number
  next_review_at: string
}

export type VocabularyReviewRequest = {
  vocabulary_id: string
  rating: number
}

export const vocabularyApi = {
  daily: () => apiRequest<VocabularyItem[]>({ path: '/vocabulary/daily-review', method: 'GET' }),
  review: (body: VocabularyReviewRequest) => apiRequest<any>({ path: '/vocabulary/review', method: 'POST', body }),
}
