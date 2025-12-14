const { test, expect } = require('@playwright/test');

test('open client modal and save', async ({ page, request }) => {
  // Assumes backend running at /api and frontend served
  await page.goto('/');
  // ensure clients tab
  await page.click('text=Clients');
  // wait for client cards to load
  await page.waitForSelector('.card, .data-card');

  const firstCard = await page.locator('.data-card').first();
  await firstCard.click();

  // modal should appear
  await page.waitForSelector('.modal-overlay, .modal, [id^="form-modal"]', { timeout: 2000 });

  // edit name
  const nameInput = page.locator('#client-name');
  await expect(nameInput).toBeVisible();
  const old = await nameInput.inputValue();
  await nameInput.fill(old + ' X');

  // click save
  await page.click('button:has-text("Save"), button:has-text("Сохранить"), #modal-save-btn');

  // wait for modal to close
  await page.waitForTimeout(500);
});