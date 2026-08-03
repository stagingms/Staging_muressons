// Standalone Playwright config for the real-browser accessibility pass.
// Kept separate so it cannot interfere with the jest suites.
const { defineConfig } = require('@playwright/test');
module.exports = defineConfig({
  testDir: './e2e',
  timeout: 90_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  workers: 1,
  reporter: [['list']],
  use: {
    baseURL: process.env.A11Y_BASE_URL || 'http://127.0.0.1:3000',
    headless: true,
    launchOptions: { executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' },
    viewport: { width: 1280, height: 900 },
  },
});
