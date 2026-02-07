import { defineStore } from 'pinia'

import type { AuthMeResponse, RolePreference } from '../types/api'
import { authService } from '../services/auth'
import { usersService } from '../services/users'

interface AuthState {
  user: AuthMeResponse | null
  loading: boolean
  bootstrapped: boolean
  error: string | null
}

let bootstrapPromise: Promise<void> | null = null

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    loading: false,
    bootstrapped: false,
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
    async bootstrap() {
      if (this.bootstrapped) {
        return
      }
      if (bootstrapPromise) {
        await bootstrapPromise
        return
      }

      bootstrapPromise = (async () => {
        await this.fetchMe()
        this.bootstrapped = true
      })()

      try {
        await bootstrapPromise
      } finally {
        bootstrapPromise = null
      }
    },
    async setPreferredRole(role: RolePreference) {
      this.loading = true
      this.error = null
      try {
        const response = await usersService.updatePreferences(role)
        if (this.user) {
          this.user.preferred_role = response.preferred_role
        } else {
          await this.fetchMe()
        }
        return true
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Failed to update role'
        return false
      } finally {
        this.loading = false
      }
    },
  },
})
