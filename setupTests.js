import { jest } from "@jest/globals";
import "@testing-library/jest-dom";

HTMLCanvasElement.prototype.getContext = () => {};
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: jest.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // Deprecated
    removeListener: jest.fn(), // Deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

window.pageConfig = {
  baseUrl: "/",
  aboutMessage: "This is the about message",
  binderVersion: "v123.456",
  repoProviders: [
    {
      detect: {
        regex: "^(https?://github.com/)?(?<repo>.*)",
      },
      displayName: "GitHub",
      id: "gh",
      spec: { validateRegex: ".+\\/.+\\/.+" },
      ref: {
        default: "HEAD",
        enabled: true,
      },
      repo: {
        label: "GitHub repository name or URL",
        placeholder:
          "example: binder-examples/requirements or https://github.com/binder-examples/requirements",
      },
    },
    {
      displayName: "Zenodo DOI",
      id: "zenodo",
      spec: { validateRegex: "10\\.\\d+\\/(.)+" },
      ref: {
        enabled: false,
      },
      repo: {
        label: "Zenodo DOI",
        placeholder: "example: 10.5281/zenodo.3242074",
      },
    },
  ],
};
