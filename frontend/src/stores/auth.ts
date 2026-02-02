import { defineStore } from 'pinia'

import type { AuthMeResponse, RolePreference } from '../types/api'
import { authService } from '../services/auth'
import { usersService } from '../services/users'

interface AuthState {
  user: AuthMeResponse | null
  loading: boolean
  error: string | null
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    loading: false,
    error: null,
  }),
  actions: {
    async fetchMe() {
      this.loading = true
      this.error = null
      try {
        this.user = await authService.me()
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Failed to load profile'
      } finally {
        this.loading = false
      }
    },
    async setPreferredRole(role: RolePreference) {
      this.loading = true
      this.error = null
      try {
        const response = await usersService.updatePreferences(role)
        if (this.user) {
          this.user.preferred_role = response.preferred_role
        }
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Failed to update role'
      } finally {
        this.loading = false
      }
    },
  },
})
