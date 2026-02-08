import { describe, expect, it } from 'vitest'

import { toWalletFriendlyAddress } from '../utils/tonAddress'

describe('toWalletFriendlyAddress', () => {
  it('converts raw address into wallet-style friendly format', () => {
    const raw = '0:1111111111111111111111111111111111111111111111111111111111111111'
    const friendly = toWalletFriendlyAddress(raw)

    expect(friendly).toBe('EQAREREREREREREREREREREREREREREREREREREREREREeYT')
  })

  it('returns original value when input is not raw format', () => {
    const value = 'EQAREREREREREREREREREREREREREREREREREREREREREeYT'
    expect(toWalletFriendlyAddress(value)).toBe(value)
  })
})
