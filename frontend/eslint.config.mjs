import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";
import prettierConfig from "eslint-config-prettier";

/**
 * Enterprise-Grade ESLint Configuration
 *
 * Built on top of Next.js recommended configs with additional strict rules for:
 * - TypeScript type safety
 * - React best practices
 * - Accessibility (WCAG 2.1 AA)
 * - Code quality standards
 */

const eslintConfig = defineConfig([
  // Base Next.js configs (includes React, React Hooks, JSX A11y, TypeScript)
  ...nextVitals,
  ...nextTs,
  prettierConfig, // Disables ESLint rules that conflict with Prettier

  // Global ignores
  globalIgnores([
    ".next/**",
    "out/**",
    "build/**",
    "dist/**",
    "node_modules/**",
    ".git/**",
    "next-env.d.ts",
    "*.config.js",
    "*.config.mjs",
    "pnpm-lock.yaml",
  ]),

  // Additional strict rules
  {
    files: ["**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx"],

    rules: {
      // ============================================
      // TypeScript Strict Rules
      // ============================================
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-unused-vars": [
        "error",
        {
          argsIgnorePattern: "^_",
          varsIgnorePattern: "^_",
          caughtErrorsIgnorePattern: "^_",
        },
      ],
      "@typescript-eslint/no-non-null-assertion": "error",
      "@typescript-eslint/consistent-type-imports": [
        "warn",
        {
          prefer: "type-imports",
          fixStyle: "separate-type-imports",
        },
      ],

      // ============================================
      // React Best Practices
      // ============================================
      "react/prop-types": "off", // We use TypeScript
      "react/react-in-jsx-scope": "off", // Not needed in Next.js
      "react/self-closing-comp": "warn",
      "react/jsx-curly-brace-presence": [
        "warn",
        { props: "never", children: "never" },
      ],
      "react/jsx-boolean-value": ["warn", "never"],

      // ============================================
      // Code Quality
      // ============================================
      "no-console": [
        "error",
        {
          allow: ["warn", "error"],
        },
      ],
      "no-debugger": "error",
      "no-alert": "warn",
      "no-var": "error",
      "prefer-const": "error",
      "prefer-arrow-callback": "warn",
      "prefer-template": "warn",
      eqeqeq: ["error", "always", { null: "ignore" }],
      curly: ["error", "all"],
      complexity: ["warn", 15],
      "max-lines": [
        "warn",
        {
          max: 400,
          skipBlankLines: true,
          skipComments: true,
        },
      ],
      "max-depth": ["warn", 4],
      "no-nested-ternary": "warn",
      "no-unneeded-ternary": "warn",
      "no-else-return": "warn",

      // ============================================
      // Import Organization (alphabetical, grouped)
      // ============================================
      "sort-imports": [
        "warn",
        {
          ignoreCase: true,
          ignoreDeclarationSort: true,
        },
      ],
    },
  },

  // Relaxed rules for config files
  {
    files: ["*.config.ts", "*.config.js", "*.config.mjs"],
    rules: {
      "@typescript-eslint/no-var-requires": "off",
      "no-console": "off",
    },
  },

  // Relaxed rules for test files
  {
    files: ["**/__tests__/**/*", "**/*.test.*", "**/*.spec.*"],
    rules: {
      "@typescript-eslint/no-explicit-any": "warn",
      "max-lines": "off",
      "no-console": "off",
    },
  },
]);

export default eslintConfig;
