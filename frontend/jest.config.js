/** @type {import('jest').Config} */
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['@testing-library/jest-dom'],
  moduleNameMapper: {
    '^@openedx/paragon$': '<rootDir>/__mocks__/@openedx/paragon.js',
  },
};
