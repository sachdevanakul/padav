import { create } from 'zustand'
import { createJSONStorage, persist } from 'zustand/middleware'
import type { User } from '../services/api'

type AuthState = {
  accessToken: string | null
  refreshToken: string | null
  user: User | null
  setTokens: (accessToken: string, refreshToken: string) => void
  setUser: (user: User) => void
  clear: () => void
}

export const authStore = create<AuthState>()(persist((set) => ({
  accessToken: null,
  refreshToken: null,
  user: null,
  setTokens: (accessToken, refreshToken) => set({ accessToken, refreshToken }),
  setUser: (user) => set({ user }),
  clear: () => set({ accessToken: null, refreshToken: null, user: null }),
}), {
  name: 'padav-session',
  storage: createJSONStorage(() => sessionStorage),
}))
