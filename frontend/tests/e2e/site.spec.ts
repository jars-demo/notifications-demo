import { expect, test } from '@playwright/test'

test('home shows the manifest and opens chapter 01', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Once, in order, on time.')
  const manifest = page.locator('section', { has: page.locator('#chapters') })
  await expect(manifest.locator('ol > li')).toHaveCount(8)
  await expect(manifest).toContainText('The login code that came too late')
  await expect(page.locator('section', { has: page.locator('#learn') }).locator('li')).toHaveCount(
    6,
  )

  await page.getByRole('link', { name: 'Start chapter 01' }).click()
  await expect(page).toHaveURL(/\/workshop\/01-the-outbox$/)
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Send after commit: the outbox')
})

test('the digest board starves the busy shop until the cap is on', async ({ page }) => {
  await page.goto('/#board')
  const board = page.locator('#board')
  await expect(board.getByTestId('Pushes')).toHaveText('1')
  await expect(board.getByTestId('Longest wait')).toHaveText('185 min')
  await expect(board).toContainText('over 30 minutes')

  await board.getByRole('button', { name: 'Debounce, cap 30' }).click()
  await expect(board.getByTestId('Pushes')).toHaveText('6')
  await expect(board.getByTestId('Longest wait')).toHaveText('30 min')

  await board.getByRole('button', { name: 'Clear' }).click()
  await expect(board.getByTestId('Pushes')).toHaveText('0')
  await board.getByRole('button', { name: '08:15, 0 updates' }).click()
  await expect(board.getByTestId('Pushes')).toHaveText('1')
  await expect(board.getByTestId('Longest wait')).toHaveText('10 min')
  await expect(board.getByRole('button', { name: '08:15, 1 update' })).toBeVisible()

  await board.getByRole('button', { name: 'Every update' }).click()
  await expect(board.getByTestId('Longest wait')).toHaveText('0 min')
  await board.getByRole('button', { name: 'Play the morning' }).click()
  await expect(board.getByRole('status')).toContainText('1 push for 1 update', { timeout: 20_000 })
})

test('Pip quizzes you, and closes with Escape', async ({ page }) => {
  await page.goto('/workshop/02-idempotency')
  await page.getByRole('button', { name: 'Ask Pip' }).click()
  const panel = page.getByRole('region', { name: "Pip's notes" })
  await expect(panel).toContainText('inside the retry loop')

  await panel.getByRole('button', { name: 'uuid4() made before the loop' }).click()
  const verdict = panel.getByRole('status').first()
  await expect(verdict).toContainText('Not quite.')
  await expect(panel.getByRole('button', { name: 'The event id' }).first()).toBeDisabled()
  // The explanation is dark text on the white panel, never light on light.
  const colours = await verdict.evaluate((node) => ({
    text: getComputedStyle(node).color,
    card: getComputedStyle(node.closest('section') as Element).backgroundColor,
  }))
  expect(colours).toEqual({ text: 'rgb(59, 58, 54)', card: 'rgb(255, 255, 255)' })

  await page.keyboard.press('Escape')
  await expect(panel).toBeHidden()
  await expect(page.getByRole('button', { name: 'Ask Pip' })).toBeFocused()
})

test('chapters render and page through in order', async ({ page }) => {
  await page.goto('/workshop')
  await expect(page.locator('main ol > li')).toHaveCount(8)

  await page.goto('/workshop/06-digests')
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Batching without silence')
  await expect(page.locator('main')).toContainText('longest wait: 604 minutes')
  await expect(page.locator('main pre').first()).toBeVisible()
  await page.getByRole('link', { name: /Next/ }).click()
  await expect(page).toHaveURL(/07-priority$/)
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Priority lanes')
})

test('nothing scrolls sideways, and code scrolls inside its block', async ({ page }) => {
  for (const path of [
    '/',
    '/workshop',
    '/workshop/04-permanent-failures',
    '/workshop/06-digests',
  ]) {
    await page.goto(path)
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    )
    expect(overflow, path).toBeLessThanOrEqual(0)
  }
  const block = page.locator('.code-block pre').first()
  expect(await block.evaluate((node) => getComputedStyle(node).overflowX)).toBe('auto')
})

test('back to top returns to the top', async ({ page }) => {
  await page.goto('/workshop/08-webhooks')
  const button = page.getByRole('button', { name: 'Back to top' })
  await expect(button).toHaveCount(0) // hidden from everyone near the top
  await page.evaluate(() => window.scrollTo(0, 3000))
  await expect(button).toBeVisible()
  await expect(button).not.toHaveAttribute('aria-hidden', 'true')
  await button.click()
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(0)
})
