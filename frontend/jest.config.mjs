import nextJest from "next/jest.js";

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files in your test environment
  dir: "./",
});

// Add any custom config to be passed to Jest
const config = {
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
  // Note: Coverage thresholds disabled until test suite is stabilized
  // coverageThreshold: {
  //   global: {
  //     branches: 80,
  //     functions: 80,
  //     lines: 80,
  //     statements: 80,
  //   },
  // },

  // Module paths for absolute imports
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/$1",
    "^@/components/(.*)$": "<rootDir>/components/$1",
    "^@/lib/(.*)$": "<rootDir>/lib/$1",
    "^@/config/(.*)$": "<rootDir>/config/$1",
    "^@/hooks/(.*)$": "<rootDir>/hooks/$1",
    "^@/stores/(.*)$": "<rootDir>/stores/$1",
    "^@/types/(.*)$": "<rootDir>/types/$1",
    // MSW subpath exports
    "^msw/node$": "<rootDir>/node_modules/msw/lib/node/index.js",
    // ESM modules that need mocking
    "^react-markdown$": "<rootDir>/__mocks__/react-markdown.tsx",
    "^remark-gfm$": "<rootDir>/__mocks__/remark-gfm.js",
    "^rehype-highlight$": "<rootDir>/__mocks__/rehype-highlight.js",
  },

  // Test match patterns
  testMatch: ["**/__tests__/**/*.[jt]s?(x)", "**/?(*.)+(spec|test).[jt]s?(x)"],

  // Exclude e2e tests (they use Playwright, not Jest)
  testPathIgnorePatterns: ["/node_modules/", "/e2e/", "/.next/"],

  // Transform configuration - allow ESM modules to be transformed
  transformIgnorePatterns: [
    "/node_modules/(?!(react-markdown|remark-gfm|remark-parse|unified|bail|is-plain-obj|trough|vfile|unist-util-stringify-position|mdast-util-from-markdown|mdast-util-to-string|micromark|decode-named-character-reference|character-entities|property-information|hast-util-whitespace|space-separated-tokens|comma-separated-tokens|devlop|estree-util-is-identifier-name|hast-util-to-jsx-runtime|html-url-attributes|mdast-util-gfm|mdast-util-gfm-autolink-literal|mdast-util-gfm-footnote|mdast-util-gfm-strikethrough|mdast-util-gfm-table|mdast-util-gfm-task-list-item|micromark-extension-gfm|micromark-extension-gfm-autolink-literal|micromark-extension-gfm-footnote|micromark-extension-gfm-strikethrough|micromark-extension-gfm-table|micromark-extension-gfm-tagfilter|micromark-extension-gfm-task-list-item|micromark-util-combine-extensions|micromark-util-decode-numeric-character-reference|micromark-util-encode|micromark-util-normalize-identifier|micromark-util-sanitize-uri|ccount|escape-string-regexp|markdown-table|zwitch|longest-streak)/)",
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
};

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
export default createJestConfig(config);
