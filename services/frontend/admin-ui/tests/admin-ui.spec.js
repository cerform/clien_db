const { test, expect } = require('@playwright/test');

test('open client modal and save', async ({ page, request }) => {
  // Assumes backend running at /api and frontend served
  await page.goto('/');
  // ensure clients tab
  await page.click('text=Clients');
  // wait for client cards to load
  await page.waitForSelector('.card, .data-card');

  // Use a selector that matches either current or legacy class names
  const firstCard = await page.locator('.card, .data-card').first();
  await firstCard.click();

  // modal should appear - wait for the Name input placeholder used in modal
  await page.waitForSelector('input[placeholder="Name"]', { timeout: 2000 });

  // edit name
  const nameInput = page.locator('input[placeholder="Name"]');
  await expect(nameInput).toBeVisible();
  const old = await nameInput.inputValue();
  await nameInput.fill(old + ' X');

  // click save
  await page.click('button:has-text("Save"), button:has-text("Сохранить"), #modal-save-btn');

  // wait for modal to close
  await page.waitForTimeout(500);
});