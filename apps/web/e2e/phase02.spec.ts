import { expect, test } from '@playwright/test'

/**
 * Phase-02 E2E: Navigation, Suche, Theme, Fallback-Logos, leere Zustände, Auswahlfluss.
 * Voraussetzung: API + Web laufen (siehe playwright.config.ts webServer).
 */
test.describe('Phase 02 Marken & Auswahl', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel('E-Mail').fill('admin@example.com')
    await page.getByLabel('Passwort').fill('AdminDemo123!')
    await page.getByRole('button', { name: 'Anmelden' }).click()
    await expect(page.getByRole('heading', { name: 'Fahrzeugmarke auswählen' })).toBeVisible()
  })

  test('Markenkacheln mit Logos und Suche', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Marke VW wählen' })).toBeVisible()
    await expect(page.locator('.dn-brand-logo img').first()).toBeVisible()
    await page.getByPlaceholder('Marke suchen…').fill('zzzz-not-a-brand')
    await expect(page.getByText('Keine Marken gefunden')).toBeVisible()
    await page.getByPlaceholder('Marke suchen…').fill('bmw')
    await expect(page.getByRole('button', { name: 'Marke BMW wählen' })).toBeVisible()
  })

  test('Theme-Persistenz Hell/Dunkel', async ({ page }) => {
    await page.getByRole('button', { name: 'Hell' }).click()
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'light')
    await page.reload()
    await expect(page.getByRole('heading', { name: 'Fahrzeugmarke auswählen' })).toBeVisible()
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'light')
    await page.getByRole('button', { name: 'Dunkel' }).click()
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')
  })

  test('Auswahlfluss Marke → Modell → Variante → VIN', async ({ page }) => {
    await page.getByRole('button', { name: 'Marke VW wählen' }).click()
    await expect(page.getByRole('heading', { name: /VW – Fahrzeugauswahl/ })).toBeVisible()
    await page.getByRole('button', { name: /Golf/ }).click()
    await page.getByRole('button', { name: /Baureihe/ }).first().click()
    await page.getByPlaceholder('z. B. WVWZZZ1JZXW000001').fill('WVWZZZ1JZXW000099')
    await page.getByRole('button', { name: 'Fahrzeug bestätigen' }).click()
    await expect(page.getByRole('heading', { name: 'Fahrzeug bestätigt' })).toBeVisible()
    await expect(page.getByRole('link', { name: 'Zur Diagnose (Simulator)' })).toBeVisible()
  })

  test('Favoriten umschalten', async ({ page }) => {
    const tile = page.locator('.dn-brand-tile').filter({ hasText: 'Audi' }).first()
    await tile.getByRole('button', { name: /Favoriten/ }).click()
    await expect(page.getByRole('heading', { name: 'Favoriten' })).toBeVisible()
  })
})
