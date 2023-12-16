module.exports = {
  env: {
    browser: true,
    jquery: true,
    node: true,
    es6: true,
    "jest/globals": true,
  },
  extends: ["eslint:recommended"],
  ignorePatterns: ["**/dist"],
  parser: "@babel/eslint-parser",
  plugins: ["jest"],
  rules: {},
};
