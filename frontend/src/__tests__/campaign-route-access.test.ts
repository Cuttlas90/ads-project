import { describe, expect, it } from 'vitest'

import router from '../router'

describe('campaign and offers route access metadata', () => {
  it('marks owner campaigns route as owner-only', () => {
    const resolved = router.resolve('/owner/campaigns')
    expect(resolved.name).toBe('owner-campaigns')
    expect(resolved.meta.access).toBe('owner')
  })

  it('marks advertiser offers route as advertiser-only', () => {
    const resolved = router.resolve('/advertiser/offers')
    expect(resolved.name).toBe('advertiser-offers')
    expect(resolved.meta.access).toBe('advertiser')
  })
})
