import type { RouteLocationRaw } from 'vue-router'

import type { RolePreference } from '../types/api'

export type RouteAccess = 'resolver' | 'shared' | 'owner' | 'advertiser'

export const PROFILE_PATH = '/profile'
export const OWNER_DEFAULT_PATH = '/owner'
export const ADVERTISER_DEFAULT_PATH = '/advertiser/marketplace'

export const resolveRoleDefaultPath = (role: RolePreference | null): RouteLocationRaw => {
  if (role === 'owner') {
    return OWNER_DEFAULT_PATH
  }
  if (role === 'advertiser') {
    return ADVERTISER_DEFAULT_PATH
  }
  return PROFILE_PATH
}

export const resolveEntryPath = (role: RolePreference | null): RouteLocationRaw => {
  return resolveRoleDefaultPath(role)
}

export const resolveAccessRedirect = (
  access: RouteAccess,
  role: RolePreference | null,
  allowNullRole = false,
): RouteLocationRaw | null => {
  if (access === 'resolver') {
    return resolveEntryPath(role)
  }

  if (access === 'shared') {
    if (role === null && !allowNullRole) {
      return PROFILE_PATH
    }
    return null
  }

  if (role === null) {
    return PROFILE_PATH
  }

  if (access !== role) {
    return resolveRoleDefaultPath(role)
  }

  return null
}

export const isForbiddenMessage = (message: string): boolean => {
  const normalized = message.toLowerCase()
  return normalized.includes('request failed (403)') || normalized.includes('not authorized')
}
