const tseslint = require('@typescript-eslint/eslint-plugin');
const parser = require('@typescript-eslint/parser');

module.exports = [{ files: ['**/*.ts'], languageOptions: { parser }, plugins: { '@typescript-eslint': tseslint }, rules: { '@typescript-eslint/no-explicit-any': 'error', 'no-eval': 'error', 'no-implied-eval': 'error' } }];
