/* @type {import('eslint').Linter.Config} */
module.exports = {
  root: true,
  env: { es2022: true, node: true, browser: false },
  parserOptions: { ecmaVersion: "latest", sourceType: "module" },
  extends: ["eslint:recommended", "plugin:import/recommended", "prettier"],
  plugins: ["import"],
  rules: {
    "no-unused-vars": ["warn", { "argsIgnorePattern": "^_", "varsIgnorePattern": "^_" }],
    "import/order": ["warn", { "newlines-between": "always", "alphabetize": { "order": "asc" } }]
  }
};
