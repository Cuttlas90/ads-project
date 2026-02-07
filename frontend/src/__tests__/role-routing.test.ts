import { describe, expect, it } from 'vitest'

import { resolveAccessRedirect, resolveEntryPath } from '../router/roleAccess'

describe('role routing helpers', () => {
  it('resolves entry path from preferred role', () => {
    expect(resolveEntryPath(null)).toBe('/profile')
    expect(resolveEntryPath('owner')).toBe('/owner')
    expect(resolveEntryPath('advertiser')).toBe('/advertiser/marketplace')
  })

  it('redirects null-role users from scoped routes to profile', () => {
    expect(resolveAccessRedirect('owner', null)).toBe('/profile')
    expect(resolveAccessRedirect('advertiser', null)).toBe('/profile')
  })

  it('redirects mismatched deep links to role defaults', () => {
    expect(resolveAccessRedirect('advertiser', 'owner')).toBe('/owner')
    expect(resolveAccessRedirect('owner', 'advertiser')).toBe('/advertiser/marketplace')
  })

  it('allows shared profile route for null role and blocks other shared routes', () => {
    expect(resolveAccessRedirect('shared', null, true)).toBeNull()
    expect(resolveAccessRedirect('shared', null, false)).toBe('/profile')
  })
})
