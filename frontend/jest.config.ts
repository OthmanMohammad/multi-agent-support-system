import type { Config } from "jest";
import nextJest from "next/jest";

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files in your test environment
  dir: "./",
});

// Add any custom config to be passed to Jest
const config: Config = {
  coverageProvider: "v8",
  testEnvironment: "jsdom",
  setupFilesAfterEnv: ["<rootDir>/jest.setup.ts"],

  // Coverage configuration - ULTRA STRICT for production quality
  collectCoverageFrom: [
    "app/**/*.{js,jsx,ts,tsx}",
    "components/**/*.{js,jsx,ts,tsx}",
    "lib/**/*.{js,jsx,ts,tsx}",
    "hooks/**/*.{js,jsx,ts,tsx}",
    "stores/**/*.{js,jsx,ts,tsx}",
    "!**/*.d.ts",
    "!**/node_modules/**",
    "!**/.next/**",
    "!**/coverage/**",
    "!**/dist/**",
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },

  // Module paths for absolute imports
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/$1",
    "^@/components/(.*)$": "<rootDir>/components/$1",
    "^@/lib/(.*)$": "<rootDir>/lib/$1",
    "^@/config/(.*)$": "<rootDir>/config/$1",
    "^@/hooks/(.*)$": "<rootDir>/hooks/$1",
    "^@/stores/(.*)$": "<rootDir>/stores/$1",
    "^@/types/(.*)$": "<rootDir>/types/$1",
  },

  // Test match patterns
  testMatch: ["**/__tests__/**/*.[jt]s?(x)", "**/?(*.)+(spec|test).[jt]s?(x)"],

  // Transform configuration
  transformIgnorePatterns: [
    "/node_modules/",
    "^.+\\.module\\.(css|sass|scss)$",
  ],

  // Clear mocks between tests automatically
  clearMocks: true,

  // Indicates whether the coverage information should be collected while executing the test
  collectCoverage: false, // Set to true in CI

  // Verbose output
  verbose: true,

  // Maximum number of workers
  maxWorkers: "50%",

  // Bail out on first test failure (strict mode)
  bail: false, // Set to true for CI

  // Error on deprecated APIs
  errorOnDeprecated: true,

  // Notify on test completion
  notify: false,

  // Stop running tests after first failure
  // bail: 1, // Uncomment for strict CI mode
};

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
export default createJestConfig(config);
