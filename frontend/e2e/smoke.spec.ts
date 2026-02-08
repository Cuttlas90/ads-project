import { test, expect } from '@playwright/test'

test('profile role picker renders for new users', async ({ page }) => {
  await page.route('**/auth/me', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 1,
        telegram_user_id: 111,
        preferred_role: null,
        ton_wallet_address: null,
        has_wallet: false,
      }),
    })
  })
  await page.goto('/')
  await expect(page).toHaveURL(/\/profile$/)
  await expect(page.getByText('Choose your role to continue.')).toBeVisible()
})
