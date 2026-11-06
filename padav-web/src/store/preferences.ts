import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type Language = 'en' | 'hi'
export type Theme = 'dark' | 'light'
type PreferenceState = {
  language: Language
  theme: Theme
  setLanguage: (language: Language) => void
  setTheme: (theme: Theme) => void
  toggleTheme: () => void
}

export const preferencesStore = create<PreferenceState>()(persist((set, get) => ({
  language: 'en',
  theme: typeof window !== 'undefined' && window.matchMedia?.('(prefers-color-scheme: light)').matches ? 'light' : 'dark',
  setLanguage: (language) => set({ language }),
  setTheme: (theme) => set({ theme }),
  toggleTheme: () => set({ theme: get().theme === 'dark' ? 'light' : 'dark' }),
}), { name: 'padav-preferences' }))
