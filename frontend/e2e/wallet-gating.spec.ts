import { expect, test } from '@playwright/test'
import type { Page } from '@playwright/test'

interface AuthMockOptions {
  preferredRole: 'owner' | 'advertiser' | null
  hasWallet: boolean
  walletAddress?: string | null
}

const mockAuth = async (page: Page, options: AuthMockOptions) => {
  await page.route('**/auth/me', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 1,
        telegram_user_id: 111,
        preferred_role: options.preferredRole,
        ton_wallet_address: options.walletAddress ?? null,
        has_wallet: options.hasWallet,
      }),
    })
  })
}

test('profile keeps role selection optional when wallet is not connected', async ({ page }) => {
  await mockAuth(page, { preferredRole: null, hasWallet: false })

  await page.route('**/users/me/preferences', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ preferred_role: 'advertiser' }),
    })
  })

  await page.goto('/profile')

  await expect(page.locator('#profile-tonconnect-button')).toBeVisible()
  await page.getByRole('button', { name: "I'm an Advertiser" }).click()
  await expect(page).toHaveURL(/\/profile$/)
})

test('funding hard-block shows modal and jumps to profile with next path', async ({ page }) => {
  await mockAuth(page, { preferredRole: 'advertiser', hasWallet: false })

  let escrowInitCalls = 0
  let tonTxCalls = 0

  await page.route('**/deals/*/escrow/init', async (route) => {
    escrowInitCalls += 1
    await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' })
  })

  await page.route('**/deals/*/escrow/tonconnect-tx', async (route) => {
    tonTxCalls += 1
    await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' })
  })

  await page.goto('/advertiser/deals/42/fund')

  await expect(page.getByText('Funding is blocked until your advertiser wallet is connected.')).toBeVisible()
  await page.getByRole('button', { name: 'Go to Profile' }).click()

  await expect(page).toHaveURL(/\/profile\?next=\/advertiser\/deals\/42\/fund$/)
  expect(escrowInitCalls).toBe(0)
  expect(tonTxCalls).toBe(0)
})

test('profile next return button navigates back to funding when wallet exists', async ({ page }) => {
  await mockAuth(page, {
    preferredRole: 'advertiser',
    hasWallet: true,
    walletAddress: '0:1111111111111111111111111111111111111111111111111111111111111111',
  })

  await page.route('**/deals/*/escrow', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        state: 'AWAITING_DEPOSIT',
        expected_amount_ton: '10',
        received_amount_ton: '0',
        deposit_confirmations: 0,
      }),
    })
  })

  await page.goto('/profile?next=/advertiser/deals/55/fund')
  await expect(page.getByRole('button', { name: 'Return to Funding' })).toBeVisible()

  await page.getByRole('button', { name: 'Return to Funding' }).click()
  await expect(page).toHaveURL(/\/advertiser\/deals\/55\/fund$/)
})
