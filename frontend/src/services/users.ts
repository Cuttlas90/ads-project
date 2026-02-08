import { api } from './api'
import type {
  RolePreference,
  UserWalletChallengeResponse,
  UserWalletSummary,
  UserWalletVerifyRequest,
} from '../types/api'

export const usersService = {
  updatePreferences(preferred_role: RolePreference) {
    return api.put<{ preferred_role: RolePreference | null }>('/users/me/preferences', {
      preferred_role,
    })
  },
  issueWalletChallenge() {
    return api.post<UserWalletChallengeResponse>('/users/me/wallet/challenge')
  },
  verifyWalletProof(payload: UserWalletVerifyRequest) {
    return api.post<UserWalletSummary>('/users/me/wallet/verify', payload)
  },
}
