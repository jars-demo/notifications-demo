import { expect, test } from '@playwright/test'

test('home shows the chapters and opens chapter 01', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { level: 1 })).toContainText('once, in order, on time')
  await expect(page.locator('section:has(#chapters) ol > li')).toHaveCount(10)

  await page.getByRole('link', { name: 'Start chapter 01' }).click()
  await expect(page).toHaveURL(/\/workshop\/01-the-outbox$/)
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Send after commit: the outbox')
})

test('the storm chart switches between strategies', async ({ page }) => {
  await page.goto('/')
  const peak = page.getByTestId('Busiest second after recovery')
  await expect(peak).toHaveText('1000')
  await expect(page.getByTestId('Last send through')).toHaveText('543 s')

  await page.getByText('With full jitter', { exact: true }).click()
  await expect(peak).toHaveText('48')
  await expect(page.getByTestId('Last send through')).toHaveText('89 s')
})

test('a chapter renders, quizzes and pages on', async ({ page }) => {
  await page.goto('/workshop/02-idempotency')
  await expect(page.locator('main')).toContainText('ada@example.com  got 4  (should get 1)')

  const quiz = page.getByRole('region', { name: /Two questions/ })
  await quiz.getByRole('button', { name: /The event id plus the purpose/ }).click()
  await expect(quiz.getByRole('status').first()).toContainText('Right.')

  await page.getByRole('link', { name: /Next/ }).click()
  await expect(page).toHaveURL(/03-permanent-failures$/)
})

test('nothing overflows the page sideways', async ({ page }) => {
  for (const url of [
    '/',
    '/workshop',
    '/workshop/04-backoff-and-jitter',
    '/workshop/10-webhooks',
  ]) {
    await page.goto(url)
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    )
    expect(overflow, url).toBeLessThanOrEqual(0)
  }
})

test('back to top appears after scrolling and returns to the top', async ({ page }) => {
  await page.goto('/workshop/05-ordering')
  const button = page.getByRole('button', { name: 'Back to top' })
  await page.evaluate(() => window.scrollTo(0, 2500))
  await expect(button).toBeVisible()
  await button.click()
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBeLessThan(50)
})
