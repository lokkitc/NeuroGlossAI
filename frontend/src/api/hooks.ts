import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ApiError } from './types'
import { authApi } from './auth'
import { lessonsApi } from './lessons'
import { pathApi } from './path'
import { roleplayApi } from './roleplay'
import { usersApi } from './users'
import { vocabularyApi } from './vocabulary'

export const queryKeys = {
  me: ['me'] as const,
  course: ['course', 'active'] as const,
  lessons: ['lessons', 'list'] as const,
  lessonById: (id: string) => ['lessons', 'byId', id] as const,
  dailyReview: ['vocab', 'daily'] as const,
  exportMe: ['users', 'export'] as const,
}

export function useMeQuery(enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.me,
    queryFn: () => authApi.me(),
    enabled,
  })
}

export function useActiveCourse() {
  return useQuery({
    queryKey: queryKeys.course,
    queryFn: async () => {
      try {
        return await pathApi.getActive()
      } catch (e) {
        if (e instanceof ApiError && e.status === 404) return null
        throw e
      }
    },
  })
}

export function useGenerateCourse() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: Parameters<typeof pathApi.generate>[0]) => pathApi.generate(body),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: queryKeys.course })
    },
  })
}

export function useGenerateFullCourse() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: Parameters<typeof pathApi.generateFull>[0]) => pathApi.generateFull(body),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: queryKeys.course })
      void qc.invalidateQueries({ queryKey: queryKeys.lessons })
    },
  })
}

export function useUpdateProgress() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: Parameters<typeof pathApi.updateProgress>[0]) => pathApi.updateProgress(body),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: queryKeys.course })
    },
  })
}

export function useLessonsList(params?: { skip?: number; limit?: number }) {
  return useQuery({
    queryKey: [...queryKeys.lessons, params?.skip ?? 0, params?.limit ?? 20] as const,
    queryFn: () => lessonsApi.list({ skip: params?.skip, limit: params?.limit }),
  })
}

export function useLessonById(id: string | undefined) {
  return useQuery({
    queryKey: id ? queryKeys.lessonById(id) : ['lessons', 'byId', ''] as const,
    queryFn: () => lessonsApi.getById(id as string),
    enabled: Boolean(id),
  })
}

export function useGenerateLesson() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: Parameters<typeof lessonsApi.generate>[0]) => lessonsApi.generate(body),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: queryKeys.lessons })
      void qc.invalidateQueries({ queryKey: queryKeys.course })
    },
  })
}

export function useRegenExercises() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => lessonsApi.regenExercises(id),
    onSuccess: (lesson) => {
      void qc.setQueryData(queryKeys.lessonById(lesson.id), lesson)
      void qc.invalidateQueries({ queryKey: queryKeys.lessons })
    },
  })
}

export function useRegenCore() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (params: { id: string; level?: string; generation_mode?: string }) =>
      lessonsApi.regenCore(params.id, { level: params.level, generation_mode: params.generation_mode }),
    onSuccess: (lesson) => {
      void qc.setQueryData(queryKeys.lessonById(lesson.id), lesson)
      void qc.invalidateQueries({ queryKey: queryKeys.lessons })
    },
  })
}

export function useDailyReview() {
  return useQuery({
    queryKey: queryKeys.dailyReview,
    queryFn: () => vocabularyApi.daily(),
  })
}

export function useReviewWord() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: Parameters<typeof vocabularyApi.review>[0]) => vocabularyApi.review(body),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: queryKeys.dailyReview })
    },
  })
}

export function useRoleplayChat() {
  return useMutation({
    mutationFn: (body: Parameters<typeof roleplayApi.chat>[0]) => roleplayApi.chat(body),
  })
}

export function useExportMe() {
  return useQuery({
    queryKey: queryKeys.exportMe,
    queryFn: () => usersApi.exportMe(),
  })
}

export function useResetMe() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => usersApi.resetMe(),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: queryKeys.course })
      void qc.invalidateQueries({ queryKey: queryKeys.lessons })
      void qc.invalidateQueries({ queryKey: queryKeys.dailyReview })
      void qc.invalidateQueries({ queryKey: queryKeys.exportMe })
    },
  })
}
