import js from '@eslint/js'
import tseslint from 'typescript-eslint'

export default [
  // .eslintignore 相当
  {
    ignores: [
      'node_modules/**',
      'dist/**',
      'logs/**',
      'admin-ui/**',
      'wanstage-admin/**',
      'scripts/**',
      'src/pages/**', // UIは除外（必要なら外す）
    ],
  },

  js.configs.recommended,
  ...tseslint.configs.recommended,

  {
    files: ['src/**/*.ts'],
    languageOptions: {
      parser: tseslint.parser,
      ecmaVersion: 'latest',
      sourceType: 'module',
    },
    rules: {
      '@typescript-eslint/no-require-imports': 'off',
      '@typescript-eslint/no-explicit-any': 'off',
      '@typescript-eslint/no-unused-vars': ['warn', {
        varsIgnorePattern: '^_',
        argsIgnorePattern: '^_',
        caughtErrors: 'none',
      }],
      'no-empty': ['error', { allowEmptyCatch: true }],
    },
  },
]
