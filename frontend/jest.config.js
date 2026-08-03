/** @type {import('jest').Config} */
const config = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '\\.module\\.css$': 'identity-obj-proxy',
    '\\.css$': 'identity-obj-proxy',
  },
  transformIgnorePatterns: [
    '/node_modules/(?!(framer-motion|recharts|d3-.*)/)',
  ],
  // e2e/ holds the Playwright real-browser accessibility pass, which needs a
  // running app and its own runner (playwright.a11y.config.js). Jest must not
  // try to execute it — the two suites are complementary, not alternatives.
  testPathIgnorePatterns: ['/node_modules/', '/e2e/'],
};

module.exports = config;
