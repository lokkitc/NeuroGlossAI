import { apiRequest } from './apiClient'

export type CourseLevel = {
  id: string
  order: number
  type: string
  total_steps: number
  status: string
  stars: number
}

export type CourseUnit = {
  id: string
  order: number
  topic: string
  description?: string | null
  icon?: string | null
  levels: CourseLevel[]
}

export type CourseSection = {
  id: string
  order: number
  title: string
  description?: string | null
  units: CourseUnit[]
}

export type ActiveCourseResponse = {
  enrollment_id: string
  course_template_id: string
  target_language: string
  theme?: string | null
  cefr_level: string
  sections: CourseSection[]
}

export type CourseGenerateRequest = {
  interests?: string[]
  level?: string
  regenerate?: boolean
}

export type GenerateFullRequest = {
  interests?: string[]
  level?: string
  max_topics?: number
  sleep_seconds?: number
  regenerate_path?: boolean
  force_regenerate_lessons?: boolean
  generation_mode?: string
}

export type ProgressUpdateRequest = {
  level_template_id: string
  status?: string | null
  stars?: number | null
  xp_gained?: number | null
}

export const pathApi = {
  getActive: () => apiRequest<ActiveCourseResponse>({ path: '/path/', method: 'GET' }),
  generate: (body: CourseGenerateRequest) =>
    apiRequest<ActiveCourseResponse>({ path: '/path/generate', method: 'POST', body }),
  generateFull: (body: GenerateFullRequest) =>
    apiRequest<any>({ path: '/path/generate-full', method: 'POST', body }),
  updateProgress: (body: ProgressUpdateRequest) =>
    apiRequest<Record<string, unknown>>({ path: '/path/progress', method: 'PATCH', body }),
}
