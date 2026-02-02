import { test, expect } from '@playwright/test'

test('landing renders', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText('Choose your role')).toBeVisible()
})
