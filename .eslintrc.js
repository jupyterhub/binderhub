module.exports = {
  env: {
    browser: true,
    es2021: true,
  },
  extends: ["eslint:recommended", "plugin:react/recommended"],
  ignorePatterns: ["dist"],
  overrides: [
    {
      env: {
        node: true,
      },
      files: [".eslintrc.{js,cjs}"],
      parserOptions: {
        sourceType: "script",
      },
    },
    {
      files: ["**/*.test.js", "**/*.test.jsx"],
      env: {
        jest: true,
        node: true,
      },
    },
  ],
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "module",
  },
  plugins: ["react"],
  rules: {
    "react/react-in-jsx-scope": "off",
    "react/jsx-uses-react": "off",
    // Temporarily turn off prop-types
    "react/prop-types": "off",
    "no-unused-vars": ["error", { args: "after-used" }],
  },
  ignorePatterns: [
    "jupyterhub_fancy_profiles/static/*.js",
    "webpack.config.js",
    "babel.config.js",
  ],
  settings: {
    react: {
      version: "detect",
    },
  },
};
