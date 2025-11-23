module.exports = {
  // TypeScript/JavaScript files
  "*.{js,jsx,ts,tsx}": [
    "eslint --fix",
    "prettier --write",
    "jest --bail --findRelatedTests --passWithNoTests",
  ],

  // JSON, CSS, Markdown files
  "*.{json,css,md}": ["prettier --write"],

  // Type check all TypeScript files (not just staged)
  "*.{ts,tsx}": () => "tsc --noEmit",
};
