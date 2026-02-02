import { api } from './api'
import type { RolePreference } from '../types/api'

export const usersService = {
  updatePreferences(preferred_role: RolePreference) {
    return api.put<{ preferred_role: RolePreference | null }>('/users/me/preferences', {
      preferred_role,
    })
  },
}
