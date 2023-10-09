module.exports = {
  env: {
    browser: true,
    jquery: true,
    es6: true,
    "jest/globals": true,
  },
  extends: "eslint:recommended",
  parserOptions: {
    sourceType: "module",
  },
  rules: {},
  plugins: ["jest"],
};
