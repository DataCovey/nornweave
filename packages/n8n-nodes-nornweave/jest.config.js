/** @type {import('jest').Config} */
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  testMatch: ['**/__tests__/**/*.test.ts'],
  moduleFileExtensions: ['ts', 'js', 'json'],
  modulePathIgnorePatterns: ['<rootDir>/dist/'],
  testPathIgnorePatterns: ['<rootDir>/dist/'],
  collectCoverageFrom: ['credentials/**/*.ts', 'nodes/**/*.ts', '!**/__tests__/**'],
  coverageDirectory: 'coverage',
  verbose: true,
};
