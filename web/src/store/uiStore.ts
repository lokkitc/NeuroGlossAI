import { create } from 'zustand'

type UiState = {
  sidebarCollapsed: boolean
  setSidebarCollapsed: (v: boolean) => void
  toggleSidebar: () => void
}

const LS_KEY = 'ng_ui_v1'

function safeParse(json: string | null): any {
  if (!json) return null
  try {
    return JSON.parse(json)
  } catch {
    return null
  }
}

const initial = (() => {
  const raw = safeParse(localStorage.getItem(LS_KEY))
  return {
    sidebarCollapsed: Boolean(raw?.sidebarCollapsed),
  }
})()

export const useUiStore = create<UiState>((set, get) => ({
  sidebarCollapsed: initial.sidebarCollapsed,
  setSidebarCollapsed: (v) => {
    localStorage.setItem(LS_KEY, JSON.stringify({ sidebarCollapsed: v }))
    set({ sidebarCollapsed: v })
  },
  toggleSidebar: () => {
    const next = !get().sidebarCollapsed
    localStorage.setItem(LS_KEY, JSON.stringify({ sidebarCollapsed: next }))
    set({ sidebarCollapsed: next })
  },
}))
