/**
 * WANSTAGE Node+TS 用 ESLint フラット設定（ESLint v9）
 * - .eslintignore は使わず、ignores に集約
 * - Prettier は plugin で最小連携（保存時整形はVSCodeで実施）
 */
import js from '@eslint/js';
import globals from 'globals';
import tseslint from 'typescript-eslint';
import prettier from 'eslint-plugin-prettier';

export default [
  // 無視パターン（.eslintignoreの代替）
  {
    ignores: ['node_modules/**', 'dist/**', '.vscode/**', 'package-lock.json'],
  },

  // 共通（JS/TS）: 環境・グローバル
  {
    files: ['**/*.{js,ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
      globals: { ...globals.node },
    },
    plugins: { prettier },
  },

  // ESLintの推奨ルール（JS）
  js.configs.recommended,

  // TypeScript 推奨（型情報なし・軽量）
  ...tseslint.configs.recommended,

  // 追加ルール（Prettier をエラーに昇格）
  {
    rules: {
      'prettier/prettier': 'error',
    },
  },
];
