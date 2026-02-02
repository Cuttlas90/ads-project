import { api } from './api'
import type { AuthMeResponse } from '../types/api'

export const authService = {
  me() {
    return api.get<AuthMeResponse>('/auth/me')
  },
}
