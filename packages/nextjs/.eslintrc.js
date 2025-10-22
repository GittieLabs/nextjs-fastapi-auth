module.exports = {
  parserOptions: {
    ecmaVersion: 2020,
    sourceType: 'module',
  },
  extends: [
    'eslint:recommended',
  ],
  env: {
    browser: true,
    node: true,
    es2020: true,
  },
  rules: {
    'no-unused-vars': 'off', // TypeScript handles this
    'no-undef': 'off', // TypeScript handles this
  },
  ignorePatterns: ['dist', 'node_modules', '__tests__'],
}
