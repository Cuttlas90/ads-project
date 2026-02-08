import { expect, test } from '@playwright/test'
import type { Page } from '@playwright/test'

const mockRoleEndpoints = async (page: Page, preferredRole: 'owner' | 'advertiser' | null) => {
  let role = preferredRole
  let preferenceUpdateCount = 0

  await page.route('**/auth/me', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 1,
        telegram_user_id: 111,
        preferred_role: role,
        ton_wallet_address: null,
        has_wallet: false,
      }),
    })
  })

  await page.route('**/users/me/preferences', async (route) => {
    const payload = route.request().postDataJSON() as { preferred_role?: 'owner' | 'advertiser' }
    if (payload.preferred_role === 'owner' || payload.preferred_role === 'advertiser') {
      role = payload.preferred_role
    }
    preferenceUpdateCount += 1
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ preferred_role: role }),
    })
  })

  return {
    getPreferenceUpdateCount: () => preferenceUpdateCount,
  }
}

test('first-time user stays on profile after selecting a role', async ({ page }) => {
  const mock = await mockRoleEndpoints(page, null)

  await page.goto('/')
  await expect(page).toHaveURL(/\/profile$/)

  await page.getByRole('button', { name: "I'm a Channel Owner" }).click()

  await expect(page).toHaveURL(/\/profile$/)
  await expect(page.getByRole('link', { name: 'Owner' })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Deals' })).toBeVisible()
  expect(mock.getPreferenceUpdateCount()).toBe(1)
})

test('returning users are routed directly by role', async ({ page }) => {
  await mockRoleEndpoints(page, 'owner')
  await page.goto('/')
  await expect(page).toHaveURL(/\/owner$/)
})

test('forbidden deep link redirects owner to owner default route', async ({ page }) => {
  await mockRoleEndpoints(page, 'owner')
  await page.goto('/advertiser/deals')
  await expect(page).toHaveURL(/\/owner$/)
})

test('forbidden deep link redirects advertiser to advertiser default route', async ({ page }) => {
  await mockRoleEndpoints(page, 'advertiser')
  await page.goto('/owner/deals')
  await expect(page).toHaveURL(/\/advertiser\/marketplace$/)
})
